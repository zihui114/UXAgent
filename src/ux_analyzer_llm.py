"""
UX Analyzer -  LLM 深度分析版本

使用方式:
    python ux_analyzer_llm.py --run-dir runs/2026-01-19_22-29-07_c9ca --persona persona_old.txt

API Key 會自動從 .env 檔案讀取 OPENAI_API_KEY
"""

import json
import re
import os
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from dotenv import load_dotenv
import openai


# ==================== UX Guidelines ====================

UX_GUIDELINES = """
## UX 設計標準（建議依據）

### 字號
- 中文（手機）密集閱讀：16–18 pt；說明書類：17–20 px
- 按鈕文字：> 22 px
- 字距：1–2 pt；超過標準值 0.7 pt 以上易讀性下降
- 行距：≥ 1.2 倍

### 字體
- 首選：無襯線體（Sans Serif）
- 襯線體（Serif）提升閱讀理解力
- 避免斜體（Italic）：閱讀與回憶效果差
- 粗體：應用於關鍵字回憶，適用於標題、按鈕

### 模式與顏色
- 深色字 + 淺色底
- 避免藍綠色作為關鍵資訊顏色
- 關鍵資訊避免只靠顏色呈現
- 顏色偏好順序：橘色 > 黃色 > 綠色 > 紅色 > 藍色 > 青色 > 紫色
- 中等飽和度（31.75%–41.25%）；主色調建議橘色或黃色，飽和度約 35%
- 背景使用明亮白色或淡暖色（高明度，但避免純白）
- 選單使用稍低於背景的明度；按鈕使用高飽和度色彩強調
- 嚴禁在淺色背景上使用檸檬黃等淡色系文字

### 介面
- 有用的資訊在頂部展現
- 避免快速密集的資訊輸入
- 避免巢狀或多層級選單

### 按鈕
- 觸控目標 ≥ 44×44 px
- 螢幕頂部優於底部
- 使用明顯震動或視覺回饋

### 元件
- 避免小滑桿、小開關
- 提供隨時可呼叫的「小幫手」或說明

### 圖示與線條
- 圖示線條加粗
- 圖示搭配文字說明
- 避免只用 icon 無文字

### 回饋
- 使用明顯震動或視覺回饋
- 聲音＋文字＋視覺提示並用（避免只有單一）
- 完成任務後提供正向回饋

### 認知負荷
- 動畫放慢
- 不自動跳轉頁面
- 明顯顯示目前步驟（資訊「一直看得到」，減少記憶負擔）
- 一步只做一個動作

### 提示訊息
- 清楚錯誤說明，提供「復原」與建議
- 危險與不可逆操作要說明清楚
- 盡可能可復原

### 其他
- 不限時操作（避免倒數計時壓力）
- 一次就可以感覺到好處
"""


# ==================== Persona Profile ====================

class PersonaProfile:
    """解析並儲存 persona 特徵"""

    def __init__(self, persona_file: str):
        self.raw_text = Path(persona_file).read_text(encoding='utf-8')
        self.name = self._extract_name()
        self.age = self._extract_field('Age')
        self.persona_type = self._extract_persona_type()
        self.risk_perception = self._extract_level('風險感知|Risk Perception')
        self.self_efficacy = self._extract_level('自我效能|Self-Efficacy')
        self.working_memory = self._extract_level('工作記憶容忍度|Working Memory Tolerance|Working Memory')
        self.strategy = self._extract_strategy()

    def _extract_name(self) -> str:
        # Try to find name like "Mrs. Wang" or "Mr. Chen"
        match = re.search(r'(Mrs?|Ms)\.\s+([A-Z][a-z]+)', self.raw_text)
        if match:
            return f"{match.group(1)}. {match.group(2)}"

        # Try Chinese name format
        match = re.search(r'(王|陳|李|張|林|吳|黃|周|徐|孫|馬|朱|胡|郭|何|高|羅|鄭|梁|謝|宋|唐|許|鄧|馮|韓|曹|曾|彭|蕭|蔡|潘|田|董|袁|於|余|葉|蔣|杜|蘇|魏|程|呂|丁|沈|任|姚|盧|傅|鍾|姜|崔|譚|廖|范|汪|陸|金|石|戴|賈|韋|夏|邱|方|侯|鄒|熊|孟|秦|白|江|閻|薛|尹|段|雷|黎|史|龍|陶|賀|顧|毛|郝|龔|邵|萬|錢|嚴|覃|武|戴|莫|孔|向|常)(先生|女士|太太)', self.raw_text)
        if match:
            return f"{match.group(1)}{match.group(2)}"
        
        # Try to find any name after "Name:" or "姓名:"
        match = re.search(r'(?:Name|姓名)[：:]\s*([^\n]+)', self.raw_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return "Unknown"

    def _extract_field(self, pattern: str) -> str:
        match = re.search(f'({pattern})[：:]\\s*([^\n]+)', self.raw_text, re.IGNORECASE)
        return match.group(2).strip() if match else "Unknown"

    def _extract_persona_type(self) -> str:
        text_upper = self.raw_text.upper()
        if '謹慎驗證型' in self.raw_text or 'CAUTIOUS VERIFIER' in text_upper or 'CAUTIOUS' in text_upper:
            return 'cautious_verifier'
        elif '效率導向型' in self.raw_text or 'ROUTINE BUYER' in text_upper or 'EFFICIENCY' in text_upper:
            return 'efficiency_oriented'
        elif 'OLD' in text_upper or '年長' in self.raw_text or '老年' in self.raw_text:
            return 'elderly_user'
        return 'unknown'

    def _extract_level(self, pattern: str) -> str:
        match = re.search(f'({pattern})[：:]\\s*([^\n]+)', self.raw_text, re.IGNORECASE)
        if match:
            level_text = match.group(2).upper()
            if 'HIGH' in level_text or '高' in level_text:
                return 'HIGH'
            elif 'LOW' in level_text or '低' in level_text:
                return 'LOW'
            elif 'MEDIUM' in level_text or '中' in level_text:
                return 'MEDIUM'
        return 'UNKNOWN'

    def _extract_strategy(self) -> str:
        if 'VERIFICATION-ORIENTED' in self.raw_text or '驗證導向' in self.raw_text:
            return 'verification'
        elif 'GOAL-ORIENTED' in self.raw_text or '目標導向' in self.raw_text:
            return 'goal_oriented'
        return 'unknown'

    def to_dict(self) -> Dict[str, str]:
        """轉換為字典格式"""
        return {
            'name': self.name,
            'type': self.persona_type,
            'risk_perception': self.risk_perception,
            'self_efficacy': self.self_efficacy,
            'working_memory': self.working_memory,
            'strategy': self.strategy
        }


# ==================== LLM Analyzer ====================

class LLMUXAnalyzer:
    """使用 LLM 進行智能 UX 分析"""

    def __init__(self, api_key: str = None):
        load_dotenv()
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "請提供 OpenAI API key:\n"
                "1. 在 .env 檔案中設定: OPENAI_API_KEY=your_key\n"
                "2. 或使用 --api-key 參數"
            )
        self.client = openai.OpenAI(api_key=self.api_key)

    def analyze_test_results(
        self,
        memory_trace: List[Dict],
        action_trace: List[str],
        persona: PersonaProfile,
        persona_file: str = None,
        run_dir: str = None,
        intent: str = None
    ) -> Dict[str, Any]:
        """使用 LLM 分析測試結果"""

        # 準備數據給 LLM
        analysis_data = self._prepare_analysis_data(
            memory_trace, action_trace, persona, intent
        )

        # 呼叫 LLM
        print("🤖 正在使用 GPT-4o 分析測試結果...")

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "你是一位資深的 UX 研究專家，專門為前端工程師提供可直接實作的介面改善建議。"
                            "所有建議必須依據提供的 UX 設計標準，並附上具體的 CSS 選擇器與數值，"
                            "讓工程師無需額外猜測即可執行。"
                        )
                    },
                    {
                        "role": "user",
                        "content": self._build_analysis_prompt(analysis_data)
                    }
                ],
                temperature=0.1,
                max_completion_tokens=12000,
                response_format={"type": "json_object"}
            )

            # 解析 LLM 回應
            analysis_result = self._parse_llm_response(response.choices[0].message.content)

            # 添加測試元數據
            test_metadata = {
                "persona_file": persona_file or "Unknown",
                "persona_name": persona.name,
                "persona_type": persona.persona_type,
                "risk_perception": persona.risk_perception,
                "self_efficacy": persona.self_efficacy,
                "working_memory": persona.working_memory,
                "strategy": persona.strategy,
                "run_directory": run_dir or "Unknown",
                "analysis_timestamp": datetime.now().isoformat(),
                "total_actions": analysis_data.get('total_actions', 0),
                "total_thoughts": analysis_data.get('total_thoughts', 0),
                "intent": intent or "未指定"
            }

            result_with_metadata = {"test_metadata": test_metadata}
            if 'test_metadata' in analysis_result:
                del analysis_result['test_metadata']
            result_with_metadata.update(analysis_result)

        except openai.RateLimitError:
            print("❌ API 配額已用盡或達到速率限制")
            raise
        except openai.APIError as e:
            print(f"❌ OpenAI API 錯誤: {e}")
            raise

        return result_with_metadata

    def _prepare_analysis_data(
        self,
        memory_trace: List[Dict],
        action_trace: List[str],
        persona: PersonaProfile,
        intent: str = None
    ) -> Dict[str, Any]:
        """準備給 LLM 的分析數據"""

        # 提取中文思考
        chinese_thoughts = []
        for entry in memory_trace:
            if entry.get('kind') == 'thought':
                content = entry.get('content', '')
                if any('\u4e00' <= char <= '\u9fff' for char in content):
                    chinese_thoughts.append({
                        'timestamp': entry.get('timestamp', 0),
                        'content': content
                    })

        # 解析動作序列
        actions = []
        element_info_map = {}
        for action_str in action_trace:
            try:
                action = json.loads(action_str)
                if isinstance(action, dict) and "action" in action:
                    actual_action = action["action"]
                    element_info = action.get("element_info", {})
                    target_id = actual_action.get("target", "")
                    if target_id and element_info:
                        element_info_map[target_id] = element_info
                    actions.append(actual_action)
                else:
                    actions.append(action)
            except:
                pass

        # 精確統計動作次數
        target_click_count = {}
        for action in actions:
            target = action.get('target', '')
            if target:
                target_click_count[target] = target_click_count.get(target, 0) + 1

        # 建立動作序列摘要
        action_summary = []
        for i, action in enumerate(actions):
            action_summary.append({
                'step': i + 1,
                'target': action.get('target', ''),
                'description': action.get('description', ''),
                'action_type': action.get('action', 'click')
            })

        # 找出重複點擊的元素
        repeated_clicks = {k: v for k, v in target_click_count.items() if v >= 2}

        # 除錯輸出
        print(f"\n📍 提取到 {len(element_info_map)} 個元素的資訊映射")
        if element_info_map:
            print("範例元素資訊:")
            for target_id, info in list(element_info_map.items())[:3]:
                print(f"  - {target_id}: class='{info.get('class', '')}', id='{info.get('id', '')}', tag='{info.get('tag', '')}'")
        else:
            print("⚠️ 警告：未提取到任何元素資訊！")

        return {
            'persona_info': persona.to_dict(),
            'persona_text_excerpt': persona.raw_text[:1500],
            'intent': intent or "未指定",
            'total_actions': len(actions),
            'actions': actions,
            'element_info_map': element_info_map,
            'chinese_thoughts': chinese_thoughts,
            'total_thoughts': len(chinese_thoughts),
            'target_click_count': target_click_count,
            'action_summary': action_summary,
            'repeated_clicks': repeated_clicks,
        }

    def _build_analysis_prompt(self, data: Dict[str, Any]) -> str:
        """構建給 LLM 的分析 prompt"""

        prompt = f"""# 任務說明

## 測試 Intent（任務目標）
{data['intent']}

**任務成功判定標準**：
- ✅ 成功：使用者完整執行了 intent 所描述的所有步驟，並在指定停止點停止操作
- ❌ 失敗：使用者未能完成 intent 的核心目標（例如未成功加入購物車、中途放棄）
- 請根據動作序列與使用者想法來判定，不可自行推測

---

# Persona 資訊
- **姓名**: {data['persona_info']['name']}
- **類型**: {data['persona_info']['type']}
- **風險感知**: {data['persona_info']['risk_perception']}
- **自我效能**: {data['persona_info']['self_efficacy']}
- **工作記憶**: {data['persona_info']['working_memory']}
- **任務策略**: {data['persona_info']['strategy']}

## Persona 特徵描述
{data['persona_text_excerpt']}

---

{UX_GUIDELINES}

---

# 測試數據

## 🔥 精確統計數據（只能引用這些數字，禁止編造）

### 總動作次數
**{data['total_actions']} 個動作**

### 每個 target 的點擊次數
```json
{json.dumps(data.get('target_click_count', {}), ensure_ascii=False, indent=2)}
```

### 重複點擊的元素（點擊 >= 2 次）
```json
{json.dumps(data.get('repeated_clicks', {}), ensure_ascii=False, indent=2)}
```

### 動作序列摘要
```json
{json.dumps(data.get('action_summary', [])[:30], ensure_ascii=False, indent=2)}
```

---

## 📍 元素資訊映射（真實的 HTML class/id）

⚠️ **這是最重要的資料！** 以下是真實的 HTML 元素資訊，在建議中必須使用這些真實的 class 和 id：

```json
{json.dumps(data.get('element_info_map', {}), ensure_ascii=False, indent=2)}
```

 **如何使用**：
 1. 找到對應的 target ID（例如 "item5"）
 2. 使用其中的 `class` 欄位作為 CSS 選擇器
 3. **重要：簡化選擇器**
@@
 5. **絕對不要猜測或編造 class 名稱**
+
+⚠️ **輸出規則補充（非常重要）**：
+在所有改善建議中，請同時輸出：
+- 一個「建議使用的簡化 CSS selector」（給工程師實作）
+- 以及對應的「完整原始 DOM 資訊（raw class / tag）」作為證據
+
+請注意：
+- 簡化 selector 與 raw class 必須來自同一個 target_id
+- raw class 必須完整逐字輸出，不可省略、不可重組

---

## 💭 使用者內心想法（最重要的數據！）

共 {data['total_thoughts']} 條想法：

```json
{json.dumps(data['chinese_thoughts'], ensure_ascii=False, indent=2)}
```

---

# 分析要求

## 步驟 1：判定任務是否成功

對照上方「測試 Intent」，逐步確認使用者是否完成所有關鍵步驟：
- 檢查動作序列，確認每個 intent 子任務是否被執行
- 檢查使用者想法，確認是否在完成前放棄
- 給出 true/false 判斷，並說明依據（不可猜測）

## 步驟 2：深度分析使用者行為

逐條閱讀所有內心想法，找出：
1. 重複出現的疑慮或困惑
2. 未被滿足的需求
3. 放棄的原因（如果任務未完成）
4. 心理變化演進

## 步驟 3：識別 UX 問題

每個問題必須包含：
1. 具體的問題描述
2. 引用至少 1-2 條使用者想法（完整原文）
3. 從「精確統計數據」中引用點擊次數
4. 嚴重程度判斷（CRITICAL/HIGH/MEDIUM/LOW）
5. 對照上方 UX 設計標準，標注違反了哪一條規範

## 步驟 4：產生改善建議

每個建議必須：
1. 對應到 UX 設計標準中的具體規範（標注條目）
2. 標示優先級（P0/P1/P2）
3. 標示【頁面】和【元素位置】
4. 提供可直接給前端工程師執行的 CSS 變更（使用元素資訊映射的真實 class/id）

**CSS 建議格式範例**：
```
【產品頁】的 button.add-to-cart (target='item12', class='add-to-cart')：
- 將 font-size 從 14px 改為 22px（依據：按鈕文字 > 22px 標準）
- 將 min-width/min-height 改為 44px（依據：觸控目標 ≥ 44×44 px）
- 將 background-color 改為高飽和橘色（依據：按鈕使用高飽和度色彩強調）
```

---

# 輸出格式（JSON）

```json
{{
  "執行摘要": {{
    "任務完成": true/false,
    "Intent": "（原始 intent 文字）",
    "完成依據": "說明動作序列中哪些步驟對應 intent，以及最終是否達成",
    "關鍵洞察": "最重要的發現"
  }},
  "UX問題": [
    {{
      "標題": "問題標題",
      "嚴重程度": "CRITICAL/HIGH/MEDIUM/LOW",
      "類別": "導航/資訊呈現/互動回饋/信任建立/字體排版/顏色對比/按鈕設計/認知負荷/其他",
      "違反UX標準": "對照 UX 設計標準，說明違反了哪一條（例如：按鈕觸控目標 < 44×44 px）",
      "描述": "具體的問題描述",
      "使用者想法": [
        "使用者想法原文1",
        "使用者想法原文2",
        "使用者想法原文3"
      ],
      "影響": "此問題對使用者體驗的影響",
      "證據": "從精確統計引用：點擊 target='itemXX' 共 X 次"
    }}
  ],
  "改善建議": [
    {{
      "優先級": "P0/P1/P2",
      "標題": "建議標題",
      "類別": "對應問題的類別",
      "對應UX標準": "本建議對應的 UX 設計標準條目（例如：觸控目標 ≥ 44×44 px）",
      "理由": "為什麼要這樣做，以及符合哪條 UX 標準",
      "具體行動": [
        "【頁面名稱】的【元素位置】（class='.real-class', target='itemXX'）：具體變更"
      ],
      "CSS變更": [
        {{
            "target_id": "itemXX",
            "raw_dom": {{
             "tag": "button",
             "class": "sale-page-btn core-btn add-to-cart-btn custom-btn cms-secondBtnBgColor cms-secondBtnTextColor cms-secondBtnBorderColor",
             "id": ""
           }},
                "選擇器": ".add-to-cart-btn",
                "選擇器說明": "完整標出class名稱",
                "屬性": "font-size",
                "目前值": "14px",
                "建議值": "22px",
                "對應UX標準": "按鈕文字 > 22px",
                "原因": "提升按鈕可讀性，符合 UX 標準"
        }}
      ],
      "預期效果": "量化的預期效果"
    }}
  ]
}}
```

**檢查清單**：
✅ 任務完成判定來自動作序列比對 intent，有明確依據？
✅ 所有點擊次數來自精確統計數據？
✅ CSS 選擇器來自元素資訊映射的真實 class？
✅ 每個問題都引用了 3+ 條使用者想法？
✅ 每個 UX 問題都標注違反的 UX 設計標準？
✅ 每個建議都標注對應的 UX 設計標準條目？
✅ 建議夠具體（有實際的 CSS 屬性和數值）？

請直接輸出 JSON。
"""
        return prompt

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """解析 LLM 的 JSON 回應"""
        try:
            return json.loads(response_text.strip())
        except json.JSONDecodeError as e:
            print(f"❌ 解析 LLM 回應失敗: {e}")
            print(f"回應內容:\n{response_text[:500]}...")
            return {
                "error": "Failed to parse LLM response",
                "raw_response": response_text
            }


# ==================== Report Generator ====================

def generate_markdown_report(analysis: Dict[str, Any], persona: PersonaProfile, run_dir: Path) -> str:
    """根據 LLM 分析結果產生 Markdown 報告"""

    test_metadata = analysis.get('test_metadata', {})

    report = f"""# UX 深度分析報告

## 📋 測試資訊

| 項目 | 內容 |
|------|------|
| **測試目錄** | {test_metadata.get('run_directory', run_dir.name)} |
| **Persona 檔案** | {test_metadata.get('persona_file', 'N/A')} |
| **Persona 姓名** | {test_metadata.get('persona_name', persona.name)} |
| **Persona 類型** | {test_metadata.get('persona_type', persona.persona_type)} |
| **分析時間** | {test_metadata.get('analysis_timestamp', datetime.now().isoformat())} |
| **總操作次數** | {test_metadata.get('total_actions', 'N/A')} |
| **總思考次數** | {test_metadata.get('total_thoughts', 'N/A')} |
| **測試 Intent** | {test_metadata.get('intent', 'N/A')} |

---

## 📊 執行摘要

### 任務完成狀態
- **Intent**: {analysis.get('執行摘要', {}).get('Intent', 'N/A')}
- **完成**: {'✅ 是' if analysis.get('執行摘要', {}).get('任務完成') else '❌ 否'}
- **完成依據**: {analysis.get('執行摘要', {}).get('完成依據', 'N/A')}

### 關鍵洞察
> {analysis.get('執行摘要', {}).get('關鍵洞察', 'N/A')}

---

## 🚨 發現的 UX 問題

"""

    for i, issue in enumerate(analysis.get('UX問題', []), 1):
        severity_emoji = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢'
        }.get(issue.get('嚴重程度', 'MEDIUM'), '⚪')

        report += f"""
### {severity_emoji} 問題 {i}: {issue.get('標題', 'Unknown')}

- **嚴重程度**: {issue.get('嚴重程度', 'N/A')}
- **類別**: {issue.get('類別', 'N/A')}
- **違反 UX 標準**: {issue.get('違反UX標準', 'N/A')}

**描述**:
{issue.get('描述', 'N/A')}

**使用者內心想法**:
"""
        for thought in issue.get('使用者想法', []):
            report += f'> "{thought}"\n\n'

        report += f"""
**影響**:
{issue.get('影響', 'N/A')}

**證據**:
{issue.get('證據', 'N/A')}

---
"""

    report += """
## 💡 改善建議

"""

    priority_order = {'P0': 1, 'P1': 2, 'P2': 3}
    recommendations = sorted(
        analysis.get('改善建議', []),
        key=lambda x: priority_order.get(x.get('優先級', 'P2'), 999)
    )

    for i, rec in enumerate(recommendations, 1):
        priority_emoji = {
            'P0': '🔥',
            'P1': '⚡',
            'P2': '📅'
        }.get(rec.get('優先級', 'P2'), '📌')

        report += f"""
### {priority_emoji} 建議 {i}: {rec.get('標題', 'Unknown')}

- **優先級**: {rec.get('優先級', 'N/A')}
- **類別**: {rec.get('類別', 'N/A')}
- **對應 UX 標準**: {rec.get('對應UX標準', 'N/A')}

**理由**:
{rec.get('理由', 'N/A')}

**具體行動**:
"""
        for action in rec.get('具體行動', []):
            report += f"- {action}\n"

        # CSS 變更清單
        if rec.get('CSS變更'):
            report += "\n**CSS 變更明細**:\n\n"
            for idx, css_change in enumerate(rec['CSS變更'], 1):
                target_id = css_change.get('target_id', 'N/A')
                selector = css_change.get('選擇器', 'N/A')
                raw_dom = css_change.get('raw_dom', {}) #顯示 raw DOM
                raw_class = raw_dom.get('class', 'N/A')
                raw_tag = raw_dom.get('tag', 'N/A')
                raw_id = raw_dom.get('id', '')
                property_name = css_change.get('屬性', 'N/A')
                current = css_change.get('目前值', 'N/A')
                recommended = css_change.get('建議值', 'N/A')
                reason = css_change.get('原因', 'N/A')
                ux_standard = css_change.get('對應UX標準', 'N/A')

                report += f"""
<details>
<summary><strong>變更 {idx}</strong>: <code>{property_name}</code> ({target_id})</summary>

- **Target ID**: `{target_id}`
- **CSS 選擇器（建議）**: `{selector}`
- **原始 DOM tag**: `{raw_tag}`
- **原始 DOM class**: `{raw_class}`
- **原始 DOM id**: `{raw_id}`
- **屬性**: `{property_name}`
- **目前值**: {current}
- **建議值**: {recommended}
- **對應 UX 標準**: {ux_standard}
- **原因**: {reason}

**使用方式**:
```css
{selector} {{
  {property_name}: {recommended};
}}
```

</details>

"""

        report += f"""
**預期效果**:
{rec.get('預期效果', 'N/A')}

---
"""

    report += f"""
---

**報告產生時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析工具**: UX Analyzer LLM Deep Analysis v1.0
"""

    return report


# ==================== Main ====================

def main():
    parser = argparse.ArgumentParser(description='UX 分析器 - 純 LLM 深度分析')
    parser.add_argument('--run-dir', required=True, help='測試結果目錄')
    parser.add_argument('--persona', required=True, help='Persona 檔案路徑')
    parser.add_argument('--intent', help='測試任務目標描述（用於判定任務成功與否）')
    parser.add_argument('--api-key', help='OpenAI API key（或在 .env 中設定）')
    parser.add_argument('--output', help='輸出報告路徑')

    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    memory_trace_file = run_dir / 'memory_trace.json'
    action_trace_file = run_dir / 'action_trace.json'
    persona_file = Path(args.persona)

    # 檢查檔案
    if not memory_trace_file.exists():
        print(f"❌ 找不到 memory_trace.json: {memory_trace_file}")
        return
    if not action_trace_file.exists():
        print(f"❌ 找不到 action_trace.json: {action_trace_file}")
        return
    if not persona_file.exists():
        print(f"❌ 找不到 persona 檔案: {persona_file}")
        return

    print(f"📊 開始 LLM 深度分析...")
    print(f"   測試目錄: {run_dir}")
    print(f"   Persona: {persona_file}")
    if args.intent:
        print(f"   Intent: {args.intent[:80]}{'...' if len(args.intent) > 80 else ''}")

    # 讀取數據
    with open(memory_trace_file, 'r', encoding='utf-8') as f:
        memory_trace = json.load(f)

    with open(action_trace_file, 'r', encoding='utf-8') as f:
        action_trace = json.load(f)

    # 解析 persona
    persona = PersonaProfile(str(persona_file))
    print(f"\n👤 Persona: {persona.name} ({persona.persona_type})")

    # 初始化 LLM 分析器
    try:
        analyzer = LLMUXAnalyzer(api_key=args.api_key)
    except ValueError as e:
        print(f"\n❌ {e}")
        return

    # 執行分析
    try:
        analysis_result = analyzer.analyze_test_results(
            memory_trace=memory_trace,
            action_trace=action_trace,
            persona=persona,
            persona_file=persona_file.name,
            run_dir=run_dir.name,
            intent=args.intent
        )
    except Exception as e:
        print(f"\n❌ 分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return

    # 檢查是否有錯誤
    if 'error' in analysis_result:
        print(f"\n❌ LLM 分析出錯")
        print(f"錯誤: {analysis_result.get('error')}")
        print(f"\n原始回應:\n{analysis_result.get('raw_response', '')[:1000]}...")
        return

    # 儲存 JSON 結果
    json_output = args.output or str(run_dir / 'ux_analysis_llm.json')
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON 分析結果已儲存: {json_output}")

    # 產生 Markdown 報告
    md_output = str(run_dir / 'ux_analysis_llm.md')
    report = generate_markdown_report(analysis_result, persona, run_dir)
    Path(md_output).write_text(report, encoding='utf-8')
    print(f"✅ Markdown 報告已產生: {md_output}")

    # 顯示摘要
    print("\n" + "="*60)
    print("LLM 分析摘要")
    print("="*60)

    summary = analysis_result.get('執行摘要', {})
    print(f"\n任務完成: {'✅ 是' if summary.get('任務完成') else '❌ 否'}")
    print(f"原因: {summary.get('完成原因', 'N/A')}")
    print(f"\n關鍵洞察: {summary.get('關鍵洞察', 'N/A')}")

    print(f"\n發現 {len(analysis_result.get('UX問題', []))} 個 UX 問題")
    print(f"產生 {len(analysis_result.get('改善建議', []))} 項改善建議")

    print(f"\n📄 完整報告請見: {md_output}")


if __name__ == '__main__':
    main()