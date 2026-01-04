# UX Analyzer 使用指南

## 概述

UX Analyzer 是一個自動化工具，用於分析 persona 測試結果並產生針對性的 UX 改善建議。它會：

1. **分析行為模式**：檢測重複動作、困惑訊號、導航問題
2. **理解 Persona 特徵**：讀取 persona 檔案的認知特性
3. **產生針對性建議**：根據 persona 類型客製化 UX 改善方向

## 工作流程

### 1. 執行 Persona 測試

使用現有的測試命令：

```bash
uv run -m src.simulated_web_agent.main \
  --persona persona_routine_buyer_nianjia.txt \
  --intent "加入一組娘家雞精到購物車" \
  --start-url https://www.ftvmall.com.tw/ \
  --max-steps 20 \
  --headed
```

測試結果會儲存在 `runs/YYYY-MM-DD_HH-MM-SS_XXXX/` 目錄下。

### 2. 執行 UX 分析

測試完成後，立即執行 UX 分析：

```bash
python src/ux_analyzer.py \
  --run-dir runs/2026-01-01_16-26-27_f19e \
  --persona persona_routine_buyer_nianjia.txt
```

**參數說明**：
- `--run-dir`: 測試結果目錄路徑
- `--persona`: Persona 檔案路徑（與測試時使用的相同）
- `--output`: （可選）自訂輸出報告路徑

### 3. 查看分析報告

分析完成後會產生兩個檔案：

1. **ux_analysis.md** - 易讀的 Markdown 報告
2. **ux_analysis.json** - 結構化的 JSON 資料

```bash
# 查看 Markdown 報告
cat runs/2026-01-01_16-26-27_f19e/ux_analysis.md

# 查看 JSON 資料
cat runs/2026-01-01_16-26-27_f19e/ux_analysis.json | python -m json.tool
```

## 報告內容解析

### Persona 資訊
顯示測試對象的關鍵特徵：
- **姓名**: 從 persona 檔案自動提取
- **類型**: efficiency_oriented（效率型）或 cautious_verifier（謹慎型）
- **關鍵特徵**: 風險感知、自我效能、工作記憶、任務策略

### 測試指標
量化的行為數據：
- **總操作次數**: Agent 執行的動作總數
- **總耗時**: 任務完成時間（毫秒）
- **操作頻率**: 平均每秒操作次數

### 發現的 UX 問題
自動檢測的問題類型：

| 問題類型 | 檢測標準 | 嚴重程度 |
|---------|---------|---------|
| `insufficient_feedback` | 重複點擊相同按鈕 ≥ 2 次 | HIGH |
| `user_confusion` | Reflections 中出現困惑關鍵詞 | HIGH |
| `excessive_scrolling` | 滾動次數 > 10 | MEDIUM-HIGH |
| `frequent_backtracking` | 返回上一頁 > 3 次 | HIGH |

### 改善建議結構

每項建議包含：
- **類別**: Visual Feedback, Information Architecture, Navigation Flow 等
- **優先級**: HIGH, MEDIUM, LOW
- **情境**: 問題發生的具體情境
- **Persona 特定考量**: 為什麼這對該 persona 特別重要
- **具體建議**: 可執行的改善措施（3-5 項）

## Persona 類型與建議差異

### Efficiency-Oriented（效率導向型）

**特徵**:
- HIGH 自我效能
- MEDIUM 風險感知
- GOAL-ORIENTED 策略

**建議重點**:
- ✅ 即時、明確的視覺回饋
- ✅ 減少不必要的步驟
- ✅ 關鍵操作按鈕要顯眼
- ✅ 快速路徑和捷徑

**範例建議**:
```
增強即時視覺回饋
- 在按鈕點擊後立即顯示大型、明顯的成功提示（至少停留 2-3 秒）
- 購物車圖示加入跳動動畫 + 數量徽章放大效果
- 按鈕狀態變化：點擊後短暫顯示「✓ 已加入」文字並變色
```

### Cautious-Verifier（謹慎驗證型）

**特徵**:
- HIGH 風險感知
- MEDIUM-LOW 自我效能
- LOW 工作記憶
- VERIFICATION-ORIENTED 策略

**建議重點**:
- ✅ 詳細、可驗證的資訊
- ✅ 清晰的視覺層級
- ✅ 降低認知負荷
- ✅ 提供確認和驗證機制

**範例建議**:
```
提供詳細且可驗證的回饋訊息
- 顯示詳細的成功訊息：「已成功加入 [商品名稱] x1 到購物車」
- 提供「查看購物車」按鈕，讓使用者可以立即驗證
- 在購物車區域顯示完整的商品縮圖和名稱
- 保持訊息顯示更長時間（5-7 秒），或提供手動關閉選項
```

## 整合到測試流程

### 方案 A: 手動執行（推薦初期）

1. 執行測試
2. 檢視測試截圖和行為
3. 執行 UX 分析
4. 閱讀報告並記錄改善建議
5. 實施 UX 改善
6. 重複測試驗證

### 方案 B: 自動化腳本

建立一個整合腳本：

```bash
#!/bin/bash
# run_persona_test_with_analysis.sh

PERSONA=$1
INTENT=$2
URL=$3

echo "🧪 執行 Persona 測試..."
RUN_DIR=$(uv run -m src.simulated_web_agent.main \
  --persona "$PERSONA" \
  --intent "$INTENT" \
  --start-url "$URL" \
  --max-steps 20 \
  --headed | grep -oP 'runs/\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_\w+')

echo "📊 執行 UX 分析..."
python src/ux_analyzer.py \
  --run-dir "$RUN_DIR" \
  --persona "$PERSONA"

echo "✅ 完成！報告位置: $RUN_DIR/ux_analysis.md"
```

使用方式：
```bash
./run_persona_test_with_analysis.sh \
  persona_routine_buyer_nianjia.txt \
  "加入一組娘家雞精到購物車" \
  https://www.ftvmall.com.tw/
```

## 進階使用

### 批次分析多個測試

如果你執行了多個測試，可以批次分析：

```bash
for run_dir in runs/2026-01-01_*/; do
  echo "分析 $run_dir"
  python src/ux_analyzer.py \
    --run-dir "$run_dir" \
    --persona persona_routine_buyer_nianjia.txt
done
```

### 比較不同 Persona 的結果

```bash
# 測試 Persona A（謹慎型）
uv run -m src.simulated_web_agent.main \
  --persona persona_cautious_verifier_nianjia.txt \
  --intent "加入一組娘家雞精到購物車" \
  --start-url https://www.ftvmall.com.tw/ \
  --max-steps 20 \
  --headed

# 分析 Persona A
python src/ux_analyzer.py \
  --run-dir runs/[TIMESTAMP_A] \
  --persona persona_cautious_verifier_nianjia.txt

# 測試 Persona B（效率型）
uv run -m src.simulated_web_agent.main \
  --persona persona_routine_buyer_nianjia.txt \
  --intent "加入一組娘家雞精到購物車" \
  --start-url https://www.ftvmall.com.tw/ \
  --max-steps 20 \
  --headed

# 分析 Persona B
python src/ux_analyzer.py \
  --run-dir runs/[TIMESTAMP_B] \
  --persona persona_routine_buyer_nianjia.txt

# 比較兩份報告，找出共同問題和 persona 特定問題
```

### 匯出所有建議到單一文件

```python
import json
from pathlib import Path

all_recommendations = []

for run_dir in Path('runs').iterdir():
    json_file = run_dir / 'ux_analysis.json'
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_recommendations.append({
                'test': run_dir.name,
                'persona': data['persona_info']['name'],
                'issues': data['detected_issues'],
                'recommendations': data['recommendations']
            })

# 儲存整合報告
with open('all_ux_recommendations.json', 'w', encoding='utf-8') as f:
    json.dump(all_recommendations, f, ensure_ascii=False, indent=2)
```

## 自訂分析規則

你可以修改 `src/ux_analyzer.py` 來調整檢測標準：

### 調整重複動作閾值

```python
# 在 detect_repeated_actions() 中
if count >= 2:  # 改成 >= 3 來提高檢測門檻
    repeated.append({...})
```

### 新增困惑關鍵詞

```python
# 在 detect_confusion_signals() 中
confusion_keywords = [
    '不確定', '找不到', '沒有看到', '不清楚', '困惑',
    'unsure', 'cannot find', 'not clear', 'confused',
    '重試', 'retry', '再試', '失敗', 'failed',
    # 新增你自己的關鍵詞
    '奇怪', '怪了', '為什麼', '怎麼會'
]
```

### 新增問題類型

```python
def detect_custom_issue(self) -> List[Dict[str, Any]]:
    """自訂問題檢測"""
    issues = []

    # 例如：檢測是否過度使用搜尋功能
    search_count = sum(1 for a in self.actions if '搜尋' in a.get('content', ''))
    if search_count > 3:
        issues.append({
            'type': 'excessive_search',
            'severity': 'medium',
            'count': search_count,
            'description': '使用者過度使用搜尋功能，可能表示導航不直觀'
        })

    return issues
```

## 常見問題

### Q: 為什麼有些 persona 特徵顯示為 UNKNOWN？

A: 確保 persona 檔案中包含完整的特徵定義，格式如下：
```
Risk Perception: MEDIUM
Self-Efficacy: HIGH
Working Memory Tolerance: MEDIUM
Task Strategy: GOAL-ORIENTED
```

### Q: 如何讓分析器識別更多語言？

A: 在 `PersonaProfile._extract_name()` 中新增更多語言的正規表達式模式。

### Q: 分析結果不準確怎麼辦？

A: 檢查以下項目：
1. memory_trace.json 是否完整
2. Persona 檔案格式是否正確
3. 測試是否正常執行完畢
4. 調整檢測閾值和關鍵詞

### Q: 可以整合到 CI/CD 嗎？

A: 可以！在測試腳本中加入 UX 分析步驟，並將報告儲存為構建產物。

## 下一步

1. **測試謹慎型 Persona**: 用 `persona_cautious_verifier_nianjia.txt` 執行測試，比較建議差異
2. **建立改善追蹤**: 將 UX 建議轉換為可追蹤的任務（例如 GitHub Issues）
3. **驗證改善效果**: 實施改善後重新測試，比較行為改變
4. **擴展 Persona**: 建立更多 persona 覆蓋不同使用者類型

## 參考資源

- **Persona 設計指南**: `docs/PERSONA_DESIGN.md`（如有）
- **測試框架文件**: `README.md`
- **UX 分析器原始碼**: `src/ux_analyzer.py`
