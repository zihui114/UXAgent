import asyncio
import datetime
import json
import logging
import pathlib
import pickle
import re
import sys
import time
import uuid
from abc import ABC, abstractmethod

import openai
from typing_extensions import override

from ..agent import Agent, context
from ..executor.env import WebAgentEnv
from .profiler import TokenProfiler

logger = logging.getLogger(__name__)


class BasePolicy(ABC):
    def __init__(self):
        pass

    @abstractmethod
    async def forward(self, playwright_env: WebAgentEnv):
        """
        Args:
            playwright_env:
                WebAgentEnv object representing the current playwright environment from which
                observation can be drawn.

        Returns:
            action (`str`):
                Return serializable string of the format '{"action": <action>, ...}'
                Examples:
                    '{"action": "click", "target": "login_button"}'
                    '{"action": "select", "target": "country", "value": "US"}'
        """
        raise NotImplementedError


class OpenAIPolicy(BasePolicy):
    def __init__(self, persona, intent):
        super().__init__()
        self.client = openai.Client()
        self.short_term_memory = []
        self.previous_actions = []
        self.plan = "EMPTY"
        self.persona = persona
        self.intent = intent
        self.prompt = open(pathlib.Path(__file__).parent / "openai_prompt.txt").read(
            10000000
        )

    def forward(self, observation, available_actions):
        this_turn_prompt = f"""
### current plan: {self.plan}
### persona: {self.persona}
### intent: {self.intent}
### memories:
{self.short_term_memory}
### previous actions:
{self.previous_actions}
### current webpage:
{observation["page"]}
### current url:
{observation["url"]}
### clickable items in the webpage:
{observation["clickables"]}
"""
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": self.prompt},
                {"role": "user", "content": this_turn_prompt},
            ],
            max_tokens=1000,
            response_format={"type": "json_object"},
        )
        output = response.choices[0].message.content
        print(output)
        output = json.loads(output)
        if "current_plan" in output:
            self.plan = output["current_plan"]
        if "new_memories" in output:
            self.short_term_memory += output["new_memories"]
        self.previous_actions.append(output["action"])

        return json.dumps(output["action"])


class HumanPolicy(BasePolicy):
    def __init__(self):
        super().__init__()

    async def forward(self, observation, available_actions):
        action = input("> ")
        try:
            action, param = action.split(" ", 1)
            if param.strip():
                # change a=b,c=d to dict
                param = {a.split("=")[0]: a.split("=")[1] for a in param.split(",")}
            else:
                param = {}
        except Exception as e:
            print(e)
            print("try again")
            return self.forward(observation, available_actions)
        return json.dumps([{"type": action, **param}])


class AgentPolicy(BasePolicy):
    def __init__(self, persona, intent, output=None):
        logger.info(f"Creating AgentPolicy with persona: {persona}, intent: {intent}")
        self.agent = Agent(persona, intent)
        logger.info("Initializing step profiler...")
        self.profiler = TokenProfiler()
        logger.info("Step profiler created.")
        # self.agent.add_thought(f"I want to {intent}")
        # lets' have a run name with current time and random string to save agent checkpoints
        # 2024-02-02_05:05:05
        # if output is None:
        #     self.run_name = f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{uuid.uuid4().hex[:4]}"
        #     self.run_path = pathlib.Path() / "runs" / self.run_name
        # else:
        #     self.run_name = output
        #     self.run_path = pathlib.Path(output)
        # self.run_path.mkdir(parents=True, exist_ok=True)
        # # context.run_path.set(self.run_path)
        # (self.run_path / "persona.txt").write_text(persona)
        # (self.run_path / "intent.txt").write_text(intent)
        # self.action_trace_file = (self.run_path / "action_trace.txt").open("w")
        # self.env_trace_file = (self.run_path / "env_trace.txt").open("w")
        self.slow_loop_task = None

    async def slow_loop(self):
        while True:
            await self.agent.reflect()
            await self.agent.wonder()
            await self.agent.memory.update()

    async def forward(self, playwright_env):
        observation = await playwright_env.observation()
        observation_str = json.dumps(observation)
        available_actions = observation.get("clickable_elements")

        # self.env_trace_file.write(observation_str + "\n")
        # len_observation = self.profiler.count_tokens(observation_str)

        # if use_profiler:
        #     logger.info("Model taking a step...")
        #     logger.info(f"length of observation = {len_observation}")
        #     for k, v in observation.items():
        #         logger.info(
        #             f"length of {k} = {self.profiler.count_tokens(json.dumps(v))}"
        #         )

        if self.agent.memory.timestamp != 0:  # make parallel
            await asyncio.gather(
                self.agent.feedback(observation["html"]),
                self.agent.perceive(observation["html"]),
            )
        else:
            await self.agent.perceive(observation["html"])
        if self.slow_loop_task is None:
            self.slow_loop_task = asyncio.create_task(self.slow_loop())
        # if self.agent.memory.timestamp != 0:
        #     await self.agent.feedback(observation)
        # await self.agent.perceive(observation)
        # await self.agent.reflect()  # parallel with wonder
        # await self.agent.wonder()
        # await asyncio.gather(self.agent.reflect(), self.agent.wonder())
        await self.agent.plan()
        action = await self.agent.act(observation)
        # pickle.dump(
        #     self.agent,
        #     open(self.run_path / f"agent_{self.agent.memory.timestamp}.pkl", "wb"),
        # )
        # (self.run_path / f"memory_trace_{self.agent.memory.timestamp}.txt").write_text(
        #     "\n".join(self.agent.format_memories(self.agent.memory.memories, False))
        # )
        # (self.run_path / f"page_{self.agent.memory.timestamp}.html").write_text(
        #     observation
        #     if isinstance(observation, str)
        #     else observation.get("html", ""),
        #     encoding="utf-8",
        #     errors="replace",
        # )
        self.agent.memory.timestamp += 1
        # self.action_trace_file.write(json.dumps(action) + "\n")
        # self.action_trace_file.flush()
        # self.env_trace_file.flush()
        return json.dumps(action)

    def get_formatted_memories(self) -> str:
        """
        Return all memories of the agent as a single formatted string.

        Returns:
            str: Formatted memory trace.
        """
        if not self.agent.memory.memories:
            return ""
        return "\n".join(self.agent.format_memories(self.agent.memory.memories))

    async def close(self):
        if self.slow_loop_task is not None:
            self.slow_loop_task.cancel()
            self.slow_loop_task = None

    # def forward(self, observation, available_actions):
    #     return asyncio.run(self._forward(observation, available_actions))
