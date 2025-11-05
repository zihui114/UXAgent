import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any, Callable, Optional

from ..agent.gpt import async_chat
from ..agent.gpt import load_prompt

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def run_survey(
    trace_dirs: list[Path],
    questionnaire: dict[str, Any],
    *,
    concurrency: int = 4,
    on_progress: Optional[Callable[[int, int], None]] = None,
) -> None:
    """
    Run the survey for all memory traces found under:
      <location of this script>/surveys/memory_trace/*.txt

    Outputs JSON results to:
      <location of this script>/surveys/out/<memory_name>.json

    Args:
        questionnaire: The questionnaire dict to pass to the model.
        concurrency: Max concurrent model calls.

    Returns:
        A list of per-memory answer dictionaries.
    """
    # ---------- Small helpers (scoped to this function) ----------
    SURVEY_PROMPT = load_prompt("survey")

    def _safe_json_loads(text: str) -> Any:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning("Model did not return valid JSON; returning raw text.")
            return {"raw": text}

    async def _generate_response_dict(trace_dir: Path) -> dict[str, Any]:
        # System prompt from your prompt loader; user content is questionnaire + memory
        # with LogApiCall():
        memory_str = (trace_dir / "memory_trace.json").read_text(encoding="utf-8")
        request = [
            {"role": "system", "content": SURVEY_PROMPT},
            {
                "role": "user",
                "content": json.dumps(questionnaire) + "\n" + memory_str,
            },
        ]
        result_text = await async_chat(request, json_mode=True)
        return _safe_json_loads(result_text)

    total = len(trace_dirs)
    done = 0
    lock = asyncio.Lock()

    # Initial ping so UI can set up the bar
    if on_progress:
        try:
            on_progress(done, total)
        except Exception:
            pass

    # ---------- Answer concurrently with a semaphore ----------
    sem = asyncio.Semaphore(concurrency)

    async def _one(trace_dir: Path):
        nonlocal done
        async with sem:
            res = await _generate_response_dict(trace_dir)
            # Write per-file output
            (trace_dir / "survey_result.json").write_text(
                json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        async with lock:
            done += 1
            if on_progress:
                try:
                    on_progress(done, total)
                except Exception:
                    pass

        return res

    tasks = [_one(trace_dir) for trace_dir in trace_dirs]
    results: list[dict[str, Any]] = []
    if tasks:
        for fut in asyncio.as_completed(tasks):
            try:
                results.append(await fut)
            except Exception as e:
                logger.exception("Error processing a memory trace: %s", e)
    return results
