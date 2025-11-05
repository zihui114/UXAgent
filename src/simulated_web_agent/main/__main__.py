import asyncio
import logging
from pathlib import Path

import click
from dotenv import load_dotenv
from hydra import compose, initialize, initialize_config_dir
from omegaconf import DictConfig

from ..agent import gpt
from ..executor.env import WebAgentEnv  # Playwright env
from .experiment import _run_for_persona_and_intent
from .model import AgentPolicy  # noqa


def _load_cfg():
    here = Path(__file__).resolve().parent
    conf_dir = here.parents[2] / "conf"
    with initialize_config_dir(version_base=None, config_dir=str(conf_dir)):
        cfg = compose(config_name="base")
    return cfg


@click.command()
@click.option(
    "--record/--no-record",
    default=False,
    show_default=True,
    help="Enable or disable session recording.",
)
@click.option(
    "--headless/--headed",
    default=False,
    show_default=True,
    help="Run browser in headless or headed mode.",
)
@click.option(
    "--persona",
    default="Persona: Clara\nBackground:\nClara is a PhD student in Computer Science at a prestigious university. She is deeply engaged in research focusing on artificial intelligence and machine learning, aiming to contribute to advancements in technology that can benefit society.\n\nDemographics:\n\nAge: 28\nGender: Female\nEducation: Pursuing a PhD in Computer Science\nProfession: PhD student\nIncome: $50,000\n\nFinancial Situation:\nClara lives on her stipend as a PhD student and is careful with her spending. She prefers to save money for research-related expenses and invest in her academic pursuits.\n\nShopping Habits:\nClara dislikes shopping and avoids spending much time browsing through products. She prefers straightforward, efficient shopping experiences and often shops online for convenience. When she does shop, she looks for practicality and affordability over style or trendiness.\nSo Clara wants to shop QUICKLY and EFFICIENTLY.\n\nProfessional Life:\nClara spends most of her time in academia, attending conferences, working in the lab, and writing papers. Her commitment to her research is her main priority, and she manages her time around her academic responsibilities.\n\nPersonal Style:\nClara prefers comfortable, functional clothing, often choosing items that are easy to wear for long hours spent at her desk or in the lab. She wears medium-sized clothing and likes colors that reflect her personality\u2014mostly red, which she finds uplifting and energizing.",
    show_default=False,
    help="Persona description string.",
)
@click.option(
    "--intent",
    default="Use amazon's Rufus feature to purchase a gaming mouse",
    show_default=False,
    help="User intent for the agent.",
)
@click.option(
    "--start-url",
    default="http://www.amazon.com",
    show_default=True,
    help="Starting URL for the session.",
)
@click.option(
    "--max-steps",
    default=20,
    show_default=True,
    type=int,
    help="Maximum number of agent steps.",
)
@click.option(
    "--wait-for-login/--no-wait-for-login",
    default=False,
    show_default=True,
    help="Wait for login to complete before starting the session.",
)
@click.option(
    "--use-user-data-dir/--no-use-user-data-dir",
    default=False,
    show_default=True,
    help="User data directory for the browser.",
)
def main(
    record: bool,
    headless: bool,
    persona: str,
    intent: str,
    start_url: str,
    max_steps: int,
    wait_for_login: bool,
    use_user_data_dir: bool,
) -> None:
    """
    Run the simulated web agent using Click-based CLI options.
    """
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("LiteLLM").setLevel(logging.WARNING)
    logging.getLogger("LiteLLM Router").setLevel(logging.WARNING)
    cfg = _load_cfg()
    cfg.environment.recording.enabled = record
    cfg.environment.browser.launch_options.headless = headless
    gpt.provider = cfg.llm_provider
    # config.browser.user_data_dir
    if not use_user_data_dir:
        cfg.environment.browser.user_data_dir = None

    asyncio.run(
        _run_for_persona_and_intent(
            cfg=cfg,
            persona_info={
                "persona": persona,
                "intent": intent,
            },
            start_url=start_url,
            max_steps=max_steps,
            wait_for_login=wait_for_login,
        )
    )


if __name__ == "__main__":
    main()
