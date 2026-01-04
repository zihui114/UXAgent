# LLM 智能 UX 分析器使用指南

## 概述

`ux_analyzer_llm.py` 使用 Claude AI 智能分析測試結果，相比規則化的 `ux_analyzer.py`，它能：

- ✅ **理解中文內心想法**：分析使用者的真實困惑和疑慮
- ✅ **智能識別行為模式**：不僅是重複點擊，還能理解背後的原因
- ✅ **產生針對性建議**：根據 persona 特徵客製化改善方案
- ✅ **提供深度洞察**：理解任務失敗的根本原因

## 前置準備

### 1. 取得 Anthropic API Key

前往 https://console.anthropic.com/ 申請 API key。

### 2. 設定環境變數

```bash
# macOS/Linux
export ANTHROPIC_API_KEY=your_api_key_here

# 或加入到 ~/.zshrc 或 ~/.bashrc 永久設定
echo 'export ANTHROPIC_API_KEY=your_api_key_here' >> ~/.zshrc
source ~/.zshrc
```

### 3. 確認安裝

```bash
python -c "import anthropic; print('OK')"
```

## 使用方式

### 基本用法

```bash
python src/ux_analyzer_llm.py \
  --run-dir runs/2026-01-01_20-14-18_3a5b \
  --persona persona_cautious_verifier_nianjia.txt
```

### 指定 API Key（如果沒有設定環境變數）

```bash
python src/ux_analyzer_llm.py \
  --run-dir runs/2026-01-01_20-14-18_3a5b \
  --persona persona_cautious_verifier_nianjia.txt \
  --api-key your_api_key_here
```

### 自訂輸出路徑

```bash
python src/ux_analyzer_llm.py \
  --run-dir runs/2026-01-01_20-14-18_3a5b \
  --persona persona_cautious_verifier_nianjia.txt \
  --output custom_report.md
```

## 輸出內容

執行後會產生兩個檔案：

### 1. `ux_analysis_llm.json`

結構化的分析結果：

```json
{
  "executive_summary": {
    "task_completed": false,
    "completion_reason": "使用者無法找到健字號認證連結，因驗證需求未滿足而放棄購買",
    "key_insight": "謹慎型使用者需要權威機構背書，缺乏 TFDA 連結是致命障礙"
  },
  "behavioral_patterns": [
    {
      "pattern": "重複點擊品牌公告",
      "evidence": "連續點擊 9 次",
      "interpretation": "使用者期待找到認證資訊但連結失效或未正確回應"
    }
  ],
  "ux_issues": [
    {
      "title": "缺乏官方認證驗證入口",
      "severity": "CRITICAL",
      "category": "信任建立",
      "description": "...",
      "user_thoughts": ["那個健字號到底在哪裡..."],
      "impact": "...",
      "evidence": {...}
    }
  ],
  "recommendations": [
    {
      "priority": "P0 (立即)",
      "title": "增加健字號認證專區",
      "specific_actions": ["在產品頁面新增認證資訊區塊", "..."],
      "expected_impact": "轉換率提升 50-80%",
      "persona_alignment": "..."
    }
  ],
  "persona_insights": {...}
}
```

### 2. `ux_analysis_llm.md`

易讀的 Markdown 報告，包含：

- 📊 執行摘要（任務是否完成、關鍵洞察）
- 🔍 行為模式分析
- 🚨 發現的 UX 問題（附嚴重程度、使用者想法引用）
- 💡 改善建議（附優先級、具體行動、預期效果）
- 🎯 Persona 洞察

## LLM vs. 規則化分析對比

| 項目 | 規則化 (ux_analyzer.py) | LLM (ux_analyzer_llm.py) |
|------|-------------------------|--------------------------|
| **分析深度** | 淺層模式匹配 | 深度語義理解 |
| **中文思考** | ❌ 不分析 | ✅ 完整分析 |
| **行為解讀** | 基於規則（如「重複2次=問題」） | 智能理解背後原因 |
| **建議品質** | 模板化 | 針對性、可執行 |
| **Persona 對齊** | 有限 | 高度客製化 |
| **成本** | 免費 | API 調用費用 |
| **速度** | 快（<1秒） | 慢（10-30秒） |

## 成本估算

使用 Claude Sonnet 4：

- 輸入 token：約 5,000-10,000（取決於測試長度）
- 輸出 token：約 3,000-5,000
- 每次分析成本：約 **$0.05-0.10 USD**

## 實際範例

### 輸入

```bash
python src/ux_analyzer_llm.py \
  --run-dir runs/2026-01-01_20-14-18_3a5b \
  --persona persona_cautious_verifier_nianjia.txt
```

### 輸出（終端）

```
📊 開始 LLM 智能分析...
   測試目錄: runs/2026-01-01_20-14-18_3a5b
   Persona: persona_cautious_verifier_nianjia.txt

👤 Persona: Mrs. Wang (cautious_verifier)
🤖 正在使用 Claude 分析測試結果...
✅ JSON 分析結果已儲存: runs/2026-01-01_20-14-18_3a5b/ux_analysis_llm.json
✅ Markdown 報告已產生: runs/2026-01-01_20-14-18_3a5b/ux_analysis_llm.md

============================================================
LLM 分析摘要
============================================================

任務完成: ❌ 否
原因: 使用者無法找到健字號認證連結，因驗證需求未滿足而放棄購買

關鍵洞察: 謹慎型使用者需要權威機構背書，缺乏 TFDA 連結是購買流程的致命障礙

發現 4 個 UX 問題
產生 6 項改善建議

📄 完整報告請見: runs/2026-01-01_20-14-18_3a5b/ux_analysis_llm.md
```

## 高級用法

### 批次分析多個測試

```bash
#!/bin/bash
# analyze_all.sh

for run_dir in runs/2026-01-01_*/; do
  echo "分析 $run_dir"

  # 根據目錄名稱判斷使用哪個 persona
  if [[ $run_dir == *"cautious"* ]]; then
    persona="persona_cautious_verifier_nianjia.txt"
  else
    persona="persona_routine_buyer_nianjia.txt"
  fi

  python src/ux_analyzer_llm.py \
    --run-dir "$run_dir" \
    --persona "$persona"
done
```

### 比較兩個 Persona 的分析結果

```bash
# 分析效率型使用者
python src/ux_analyzer_llm.py \
  --run-dir runs/2026-01-01_16-26-27_f19e \
  --persona persona_routine_buyer_nianjia.txt

# 分析謹慎型使用者
python src/ux_analyzer_llm.py \
  --run-dir runs/2026-01-01_20-14-18_3a5b \
  --persona persona_cautious_verifier_nianjia.txt

# 比較兩份報告
diff runs/2026-01-01_16-26-27_f19e/ux_analysis_llm.md \
     runs/2026-01-01_20-14-18_3a5b/ux_analysis_llm.md
```

## 故障排除

### 問題 1: API Key 錯誤

```
❌ 請提供 Anthropic API key
```

**解決**：
```bash
export ANTHROPIC_API_KEY=your_key_here
# 或使用 --api-key 參數
```

### 問題 2: JSON 解析失敗

```
❌ 解析 LLM 回應失敗: Expecting property name enclosed in double quotes
```

**原因**：LLM 偶爾會產生格式錯誤的 JSON

**解決**：重新執行一次，或檢查 `raw_response` 欄位手動修正

### 問題 3: Token 超限

```
anthropic.BadRequestError: messages: text is too long
```

**原因**：測試數據太長（例如步數 > 100）

**解決**：在 `_prepare_analysis_data()` 中調整截取數量

## 最佳實踐

### 1. 何時使用 LLM 分析器

- ✅ **重要測試**：關鍵功能、高優先級 persona
- ✅ **複雜行為**：規則化分析器無法理解的模式
- ✅ **需要深度洞察**：要向團隊報告或做決策依據
- ❌ **快速迭代**：開發中的快速檢查（用規則化版本）

### 2. 結合兩種分析器

```bash
# 先用規則化版本快速檢查
python src/ux_analyzer.py --run-dir runs/... --persona ...

# 發現問題後，用 LLM 深度分析
python src/ux_analyzer_llm.py --run-dir runs/... --persona ...
```

### 3. 節省成本

- 在開發階段使用規則化分析器
- 正式測試時才使用 LLM 分析器
- 批次處理多個測試以攤平啟動成本

## 未來改進

計劃中的功能：

1. **多 Persona 對比分析**：一次分析多個 persona 的測試結果並產生對比報告
2. **時間序列分析**：追蹤同一網站在不同時間點的 UX 改善
3. **自動優先級排序**：根據影響範圍和實施成本自動排序建議
4. **視覺化報告**：產生圖表和熱力圖
5. **自訂 prompt 模板**：允許使用者客製化分析角度

## 參考資源

- **Anthropic API 文件**: https://docs.anthropic.com/
- **規則化分析器**: `src/ux_analyzer.py`
- **原始碼**: `src/ux_analyzer_llm.py`
- **範例報告**: `runs/*/ux_analysis_llm.md`
