#!/usr/bin/env python3
"""
執行 survey 對最新的測試 run 進行評估
使用 conf/runConfig.yaml 中定義的問卷
"""
import asyncio
import json
from pathlib import Path
import sys
import yaml

# 添加 src 到 path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from simulated_web_agent.main.survey import run_survey


def load_questionnaire_from_config() -> dict:
    """從 conf/runConfig.yaml 載入問卷定義"""
    config_path = Path(__file__).parent / "conf" / "runConfig.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 從 YAML 格式轉換為 survey.py 期望的格式
    questionnaire = config.get('questionnaire', {})

    # 轉換問題格式：YAML 使用 'prompt'，survey 期望 'question'
    questions = []
    for q in questionnaire.get('questions', []):
        questions.append({
            "id": q["id"],
            "question": q["prompt"],
            "type": q["type"]
        })

    return {
        "questionnaire_id": questionnaire.get("questionnaire_id", "survey"),
        "questions": questions
    }


def get_latest_run_dir() -> Path:
    """找到最新的 run 資料夾"""
    runs_dir = Path(__file__).parent / "runs"
    run_dirs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
    if not run_dirs:
        raise FileNotFoundError("No run directories found")
    return run_dirs[0]


async def main():
    # 找到最新的 run
    latest_run = get_latest_run_dir()
    print(f"📁 Latest run: {latest_run.name}")

    # 檢查 memory_trace.json 是否存在
    memory_file = latest_run / "memory_trace.json"
    if not memory_file.exists():
        print(f"❌ Error: {memory_file} not found")
        return

    print(f"✅ Found memory trace: {memory_file}")

    # 從 conf/runConfig.yaml 載入問卷
    print("\n📋 Loading questionnaire from conf/runConfig.yaml...")
    questionnaire = load_questionnaire_from_config()
    print(f"   Loaded {len(questionnaire['questions'])} questions")
    print(f"   Questionnaire ID: {questionnaire['questionnaire_id']}")

    # 執行 survey
    print("\n🔍 Running survey analysis...")
    trace_dirs = [latest_run]

    results = await run_survey(
        trace_dirs=trace_dirs,
        questionnaire=questionnaire,
        concurrency=1,
        on_progress=lambda current, total: print(f"Progress: {current}/{total}")
    )

    # 顯示結果
    print("\n" + "="*60)
    print("📊 SURVEY RESULTS")
    print("="*60)

    result_file = latest_run / "survey_result.json"
    if result_file.exists():
        result = json.loads(result_file.read_text(encoding="utf-8"))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"\n✅ Results saved to: {result_file}")
    else:
        print("❌ Survey result file not created")

    return results


if __name__ == "__main__":
    asyncio.run(main())
