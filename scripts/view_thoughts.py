#!/usr/bin/env python3
"""
快速查看測試中 Agent 的思考過程

使用方式:
    python scripts/view_thoughts.py runs/2026-01-01_16-26-27_f19e
    python scripts/view_thoughts.py  # 自動使用最新的 run
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def get_latest_run():
    """取得最新的測試目錄"""
    runs_dir = Path('runs')
    if not runs_dir.exists():
        print("❌ 找不到 runs 目錄")
        sys.exit(1)

    run_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
    if not run_dirs:
        print("❌ runs 目錄中沒有測試結果")
        sys.exit(1)

    # 按修改時間排序，取最新的
    latest = max(run_dirs, key=lambda d: d.stat().st_mtime)
    return latest


def format_timestamp(ts):
    """格式化時間戳"""
    if ts > 1e12:  # 毫秒
        ts = ts / 1000
    return datetime.fromtimestamp(ts).strftime('%H:%M:%S')


def view_thoughts(run_dir):
    """查看思考過程"""
    memory_file = run_dir / 'memory_trace.json'

    if not memory_file.exists():
        print(f"❌ 找不到 memory_trace.json: {memory_file}")
        return

    with open(memory_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"\n{'='*80}")
    print(f"測試目錄: {run_dir.name}")
    print(f"{'='*80}\n")

    # 提取所有 reflections (thoughts)
    reflections = []
    for entry in data:
        if entry.get('kind') == 'reflection':
            reflections.append(entry)

    if not reflections:
        print("ℹ️  此測試中沒有找到 reflection 記錄")
        return

    print(f"📝 總共 {len(reflections)} 條思考記錄\n")

    # 顯示每條思考
    for i, reflection in enumerate(reflections, 1):
        timestamp = reflection.get('timestamp', 0)
        content = reflection.get('content', '')

        # 嘗試解析 thoughts
        if isinstance(content, str):
            # 可能是 JSON 字串
            try:
                parsed = json.loads(content)
                if isinstance(parsed, dict) and 'thoughts' in parsed:
                    thoughts = parsed['thoughts']
                else:
                    thoughts = [content]
            except:
                thoughts = [content]
        elif isinstance(content, dict) and 'thoughts' in content:
            thoughts = content['thoughts']
        elif isinstance(content, list):
            thoughts = content
        else:
            thoughts = [str(content)]

        print(f"💭 思考 #{i} [{format_timestamp(timestamp)}]")
        print("-" * 80)

        for j, thought in enumerate(thoughts, 1):
            # 換行顯示，每行縮排
            lines = thought.strip().split('\n')
            for line in lines:
                print(f"  {j}. {line}" if len(thoughts) > 1 else f"  {line}")

        print()

    # 顯示關鍵思考（包含特定關鍵字）
    print(f"\n{'='*80}")
    print("🔍 關鍵思考（包含重要關鍵字）")
    print(f"{'='*80}\n")

    keywords = [
        '不確定', '困惑', '奇怪', '找不到', '看不到',
        '擔心', '疑慮', '風險', '安全', '驗證',
        '認證', '成分', '品質', '信譽'
    ]

    key_reflections = []
    for reflection in reflections:
        content_str = json.dumps(reflection.get('content', ''), ensure_ascii=False)
        if any(keyword in content_str for keyword in keywords):
            key_reflections.append(reflection)

    if key_reflections:
        for reflection in key_reflections:
            timestamp = reflection.get('timestamp', 0)
            content = reflection.get('content', '')
            print(f"⚠️  [{format_timestamp(timestamp)}]")

            # 高亮關鍵字
            content_str = str(content)
            for keyword in keywords:
                if keyword in content_str:
                    print(f"   關鍵字: {keyword}")
                    break

            print(f"   內容: {content_str[:200]}...")
            print()
    else:
        print("ℹ️  沒有找到包含關鍵字的思考")


def main():
    if len(sys.argv) > 1:
        run_dir = Path(sys.argv[1])
    else:
        print("🔍 未指定目錄，使用最新的測試結果...\n")
        run_dir = get_latest_run()

    if not run_dir.exists():
        print(f"❌ 目錄不存在: {run_dir}")
        sys.exit(1)

    view_thoughts(run_dir)


if __name__ == '__main__':
    main()
