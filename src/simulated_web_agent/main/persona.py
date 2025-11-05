import asyncio
import logging
import pathlib
import random
import re
from typing import Any, Awaitable, Callable, Optional

from hydra import compose, initialize, initialize_config_dir
from omegaconf import DictConfig

from ..agent import gpt

logger = logging.getLogger(__name__)


# --- utils -------------------------------------------------------------------
def parse_range(range_str: str) -> tuple[int, int]:
    m = re.match(r"(\d+)\s*-\s*(\d+)", range_str)
    if m:
        return int(m.group(1)), int(m.group(2))
    raise ValueError(f"Invalid range format: '{range_str}'")


def prepare_cumulative_distribution(ratio_dict: dict[str, float]):
    items = list(ratio_dict.items())
    total_ratio = sum(ratio_dict.values())
    cumulative, acc = [], 0.0
    for k, v in items:
        acc += v / total_ratio
        cumulative.append((acc, k))

    return cumulative


def sample_from_cumulative(cumulative):
    r = random.random()
    for prob, k in cumulative:
        if r <= prob:
            return k
    return cumulative[-1][1]  # rounding safety


def _prepare_demographics_cumulative(demographics: list[dict[str, Any]]):
    prepped: list[tuple[str, list[tuple[float, str]]]] = []
    for dim in demographics:
        name = dim.get("name")
        choices = dim.get("choices", [])
        # normalize probabilities
        total = sum(float(c.get("weight", 0.0)) for c in choices) or 1.0
        acc = 0.0
        cumulative: list[tuple[float, str]] = []
        for c in choices:
            p = float(c.get("weight", 0.0)) / total
            acc += p
            cumulative.append((acc, str(c.get("name"))))
        if cumulative:
            prepped.append((str(name), cumulative))

    return prepped


# helper of loading config file. Needed for the example persona if not provided
def _load_cfg(config_name: str = "base"):
    here = pathlib.Path(__file__).resolve().parent
    conf_dir = here.parents[2] / "conf"
    with initialize_config_dir(version_base=None, config_dir=str(conf_dir)):
        cfg = compose(config_name=config_name)
    return cfg


async def _generate_one(
    demographics_cum: list[tuple[str, list[tuple[float, str]]]],
    general_intent: str,
    example_persona: str,
    previous_personas: list[str],
    chat_fn: Callable[..., Awaitable[str]] = gpt.async_chat,
    rng_seed: int | None = None,
    sem: asyncio.Semaphore | None = None,
):
    r = random.Random(rng_seed) if rng_seed is not None else random.Random()
    # sample values for each demographic dimension
    sampled: dict[str, str] = {}
    for attr_name, cum in demographics_cum:
        choice = sample_from_cumulative(cum)
        sampled[attr_name] = str(choice)

    # for diversity: pick some previous personas as examples
    # and ensure the generated persona deviates from those
    if previous_personas:
        num_examples = min(len(previous_personas), 3)
        examples = random.sample(previous_personas, num_examples)
        example_text = "\n\n".join(examples)
    else:
        example_text = example_persona

    persona_msg = [
        {
            "role": "system",
            "content": f"""You are a helpful assistant that generates diverse personas.
                        Examples:
                        {example_text}
                        """,
        },
        {
            "role": "user",
            "content": (
                "Generate a persona using the above examples. The persona should be different from previous personas to ensure diversity.\n"
                + "The persona should:\n"
                + "\n".join([f"- have the {k} of {v}" for k, v in sampled.items()])
                + "\nProvide the persona in the same format as the examples."
                + "\nOnly output the persona, no other text."
            ),
        },
    ]

    # intent_msg = lambda persona: [
    #     {
    #         "role": "system",
    #         "content": "You output only a single, specific, actionable intent, no extra text.",
    #     },
    #     {
    #         "role": "user",
    #         "content": (
    #             f"The persona is:\n{persona}\n\n"
    #             f"Based on the general intent '{general_intent}', output ONE concrete, executable intention "
    #             f"this persona would take (e.g., buy/compare/book/choose), with enough detail to act on a website."
    #         ),
    #     },
    # ]

    async def call_chat(messages):
        if sem is None:
            return (await chat_fn(messages=messages)).strip()
        async with sem:
            return (await chat_fn(messages=messages)).strip()

    persona = await call_chat(persona_msg)
    # intent = await call_chat(intent_msg(persona))

    # add this generated persona to the example pool
    previous_personas.append(persona)

    return {"persona": persona, "intent": general_intent, **sampled}


async def generate_personas(
    demographics: list[dict[str, Any]],
    general_intent: str,
    n: int = 1,
    chat_fn: Callable[..., Awaitable[str]] = gpt.async_chat,
    max_concurrency: int = 8,
    rng_seed: int | None = None,
    on_progress: Optional[Callable[[int, int], None]] = None,
    example_text: Optional[str] = None,
) -> list[dict[str, str]]:
    """
    Concurrent persona generation using asyncio and async_chat.
    """
    demographics_cum = _prepare_demographics_cumulative(demographics)

    sem = asyncio.Semaphore(max_concurrency) if max_concurrency else None

    # base example, default to the one in config if not provided
    cfg = _load_cfg()
    base_example = cfg.example_persona
    gpt.provider = cfg.llm_provider

    if example_text and example_text != "":
        logger.info("Using custom persona example: " + example_text[:100] + "...")
        base_example = example_text
    else:
        logger.info(
            "No custom persona example provided. Using the default example to start..."
        )

    # store generated personas to use as example, ensuring diversity
    previous_personas = []

    # Wrap each task with its index so we can restore order later.
    async def _one_indexed(idx: int, seed_i: int | None):
        res = await _generate_one(
            demographics_cum,
            general_intent,
            base_example,
            previous_personas,
            chat_fn,
            seed_i,
            sem,
        )
        return idx, res

    tasks = []
    for i in range(n):
        seed_i = (rng_seed + i) if rng_seed is not None else None
        tasks.append(asyncio.create_task(_one_indexed(i, seed_i)))

    results: list[dict[str, str]] = [None] * n  # type: ignore
    done = 0

    # As each task finishes, record its result and ping progress.
    for fut in asyncio.as_completed(tasks):
        idx, res = await fut
        results[idx] = res
        done += 1
        if on_progress:
            try:
                on_progress(done, n)
            except Exception:
                pass  # progress should never crash the job

    return results
