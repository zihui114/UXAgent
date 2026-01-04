"""
UX Analyzer - 分析測試結果並產生針對 persona 的 UX 改善建議

使用方式:
    python src/ux_analyzer.py --run-dir runs/2026-01-01_16-26-27_f19e --persona persona_routine_buyer_nianjia.txt
"""

import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


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

        # Fallback to "Unknown"
        return "Unknown"

    def _extract_field(self, pattern: str) -> str:
        match = re.search(f'({pattern})[：:]\\s*([^\n]+)', self.raw_text)
        return match.group(2).strip() if match else "Unknown"

    def _extract_persona_type(self) -> str:
        if '謹慎驗證型' in self.raw_text or 'Cautious Verifier' in self.raw_text:
            return 'cautious_verifier'
        elif '效率導向型' in self.raw_text or 'Routine Buyer' in self.raw_text:
            return 'efficiency_oriented'
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


class BehaviorAnalyzer:
    """分析測試中的行為模式"""

    def __init__(self, memory_trace: List[Dict]):
        self.memory_trace = memory_trace
        self.actions = [e for e in memory_trace if e.get('kind') == 'action']
        self.observations = [e for e in memory_trace if e.get('kind') == 'observation']
        self.reflections = [e for e in memory_trace if e.get('kind') == 'reflection']

    def detect_repeated_actions(self) -> List[Dict[str, Any]]:
        """檢測重複動作（可能表示缺乏回饋）"""
        repeated = []
        action_sequence = []

        for action in self.actions:
            content = action.get('content', '')
            action_sequence.append(content)

        # 尋找連續重複的動作
        i = 0
        while i < len(action_sequence) - 1:
            current = action_sequence[i]
            count = 1
            j = i + 1

            # 檢查是否為相同或相似的動作
            while j < len(action_sequence):
                if self._is_similar_action(current, action_sequence[j]):
                    count += 1
                    j += 1
                else:
                    break

            if count >= 2:  # 重複 2 次以上
                repeated.append({
                    'action': current[:100],
                    'count': count,
                    'timestamp_start': self.actions[i].get('timestamp', 0),
                    'type': self._classify_action(current)
                })
                i = j
            else:
                i += 1

        return repeated

    def _is_similar_action(self, action1: str, action2: str) -> bool:
        """判斷兩個動作是否相似"""
        # 提取關鍵詞
        keywords1 = set(re.findall(r'[\u4e00-\u9fff]+', action1))
        keywords2 = set(re.findall(r'[\u4e00-\u9fff]+', action2))

        if keywords1 and keywords2:
            overlap = len(keywords1 & keywords2) / len(keywords1 | keywords2)
            return overlap > 0.5

        return action1 == action2

    def _classify_action(self, action: str) -> str:
        """分類動作類型"""
        if '加入購物車' in action or 'Add to Cart' in action:
            return 'add_to_cart'
        elif '搜尋' in action or 'search' in action.lower():
            return 'search'
        elif '點擊' in action or 'click' in action.lower():
            return 'navigation'
        elif '滾動' in action or 'scroll' in action.lower():
            return 'scroll'
        return 'other'

    def detect_confusion_signals(self) -> List[Dict[str, Any]]:
        """從 reflections 中檢測困惑訊號"""
        confusion_keywords = [
            '不確定', '找不到', '沒有看到', '不清楚', '困惑',
            'unsure', 'cannot find', 'not clear', 'confused',
            '重試', 'retry', '再試', '失敗', 'failed'
        ]

        signals = []
        for reflection in self.reflections:
            content = reflection.get('content', '')
            for keyword in confusion_keywords:
                if keyword in content.lower():
                    signals.append({
                        'timestamp': reflection.get('timestamp', 0),
                        'content': content[:200],
                        'keyword': keyword
                    })
                    break

        return signals

    def calculate_task_efficiency(self) -> Dict[str, Any]:
        """計算任務效率指標"""
        total_actions = len(self.actions)
        total_time = 0

        if self.actions:
            start_time = self.actions[0].get('timestamp', 0)
            end_time = self.actions[-1].get('timestamp', 0)
            total_time = end_time - start_time

        return {
            'total_actions': total_actions,
            'total_time_ms': total_time,
            'actions_per_second': total_actions / (total_time / 1000) if total_time > 0 else 0
        }

    def detect_navigation_issues(self) -> List[Dict[str, Any]]:
        """檢測導航問題（過多滾動、返回等）"""
        issues = []
        scroll_count = 0
        back_count = 0

        for action in self.actions:
            content = action.get('content', '').lower()
            if 'scroll' in content or '滾動' in content:
                scroll_count += 1
            if 'back' in content or '返回' in content or '上一頁' in content:
                back_count += 1

        if scroll_count > 10:
            issues.append({
                'type': 'excessive_scrolling',
                'count': scroll_count,
                'severity': 'medium' if scroll_count < 20 else 'high'
            })

        if back_count > 3:
            issues.append({
                'type': 'frequent_backtracking',
                'count': back_count,
                'severity': 'high'
            })

        return issues


class UXRecommendationGenerator:
    """根據 persona 特徵和行為模式產生 UX 建議"""

    def __init__(self, persona: PersonaProfile, behavior: BehaviorAnalyzer):
        self.persona = persona
        self.behavior = behavior

    def generate_recommendations(self) -> Dict[str, Any]:
        """產生完整的 UX 改善建議報告"""
        recommendations = {
            'persona_info': {
                'name': self.persona.name,
                'type': self.persona.persona_type,
                'key_traits': {
                    'risk_perception': self.persona.risk_perception,
                    'self_efficacy': self.persona.self_efficacy,
                    'working_memory': self.persona.working_memory,
                    'strategy': self.persona.strategy
                }
            },
            'detected_issues': [],
            'recommendations': [],
            'priority_actions': []
        }

        # 分析重複動作
        repeated_actions = self.behavior.detect_repeated_actions()
        if repeated_actions:
            for repeat in repeated_actions:
                issue = self._analyze_repeated_action(repeat)
                if issue:
                    recommendations['detected_issues'].append(issue)
                    recommendations['recommendations'].extend(
                        self._generate_feedback_recommendations(repeat, issue)
                    )

        # 分析困惑訊號
        confusion_signals = self.behavior.detect_confusion_signals()
        if confusion_signals:
            issue = {
                'type': 'user_confusion',
                'severity': 'high',
                'count': len(confusion_signals),
                'examples': [s['content'] for s in confusion_signals[:3]]
            }
            recommendations['detected_issues'].append(issue)
            recommendations['recommendations'].extend(
                self._generate_clarity_recommendations(confusion_signals)
            )

        # 分析導航問題
        nav_issues = self.behavior.detect_navigation_issues()
        if nav_issues:
            recommendations['detected_issues'].extend(nav_issues)
            recommendations['recommendations'].extend(
                self._generate_navigation_recommendations(nav_issues)
            )

        # 分析任務效率
        efficiency = self.behavior.calculate_task_efficiency()
        recommendations['task_metrics'] = efficiency

        # 根據 persona 類型調整建議優先級
        recommendations['priority_actions'] = self._prioritize_by_persona(
            recommendations['recommendations']
        )

        return recommendations

    def _analyze_repeated_action(self, repeat: Dict) -> Dict[str, Any]:
        """分析重複動作的原因"""
        action_type = repeat['type']
        count = repeat['count']

        if action_type == 'add_to_cart' and count >= 2:
            return {
                'type': 'insufficient_feedback',
                'severity': 'high',
                'action': repeat['action'],
                'repeat_count': count,
                'description': f'使用者重複點擊「加入購物車」{count}次，表示缺乏明確的成功回饋'
            }

        return None

    def _generate_feedback_recommendations(self, repeat: Dict, issue: Dict) -> List[Dict]:
        """針對回饋不足產生建議"""
        recs = []

        if self.persona.persona_type == 'efficiency_oriented':
            # 效率型使用者：需要即時、明確的回饋
            recs.append({
                'category': 'Visual Feedback',
                'priority': 'HIGH',
                'title': '增強即時視覺回饋',
                'description': f'{self.persona.name} 是效率導向型使用者，期望快速完成任務。重複點擊 {repeat["count"]} 次表示回饋不夠明顯。',
                'recommendations': [
                    '在按鈕點擊後立即顯示大型、明顯的成功提示（至少停留 2-3 秒）',
                    '購物車圖示加入跳動動畫 + 數量徽章放大效果',
                    '按鈕狀態變化：點擊後短暫顯示「✓ 已加入」文字並變色',
                    '考慮加入聲音提示（可選）'
                ],
                'persona_specific': f'效率型使用者（自我效能: {self.persona.self_efficacy}）需要確定性，避免重複操作浪費時間'
            })

        elif self.persona.persona_type == 'cautious_verifier':
            # 謹慎型使用者：需要詳細、可驗證的回饋
            recs.append({
                'category': 'Detailed Feedback',
                'priority': 'HIGH',
                'title': '提供詳細且可驗證的回饋訊息',
                'description': f'{self.persona.name} 是謹慎驗證型使用者，需要確認操作結果。',
                'recommendations': [
                    '顯示詳細的成功訊息：「已成功加入 [商品名稱] x1 到購物車」',
                    '提供「查看購物車」按鈕，讓使用者可以立即驗證',
                    '在購物車區域顯示完整的商品縮圖和名稱',
                    '保持訊息顯示更長時間（5-7 秒），或提供手動關閉選項'
                ],
                'persona_specific': f'謹慎型使用者（風險感知: {self.persona.risk_perception}）需要完整資訊來降低不確定性'
            })

        return recs

    def _generate_clarity_recommendations(self, signals: List[Dict]) -> List[Dict]:
        """針對困惑訊號產生建議"""
        recs = []

        if self.persona.working_memory == 'LOW':
            recs.append({
                'category': 'Information Architecture',
                'priority': 'HIGH',
                'title': '簡化資訊架構，降低認知負荷',
                'description': f'{self.persona.name} 工作記憶容忍度較低，複雜的介面會造成困惑。',
                'recommendations': [
                    '減少每個頁面的資訊量，採用分步驟引導',
                    '使用明確的視覺層級（標題、副標題、內容）',
                    '重要操作按鈕使用高對比色，避免被忽略',
                    '加入進度指示器（如：步驟 1/3）'
                ],
                'persona_specific': f'低工作記憶使用者需要清晰的路徑，避免一次處理太多資訊'
            })

        return recs

    def _generate_navigation_recommendations(self, issues: List[Dict]) -> List[Dict]:
        """針對導航問題產生建議"""
        recs = []

        for issue in issues:
            if issue['type'] == 'excessive_scrolling':
                recs.append({
                    'category': 'Layout Optimization',
                    'priority': 'MEDIUM',
                    'title': '優化頁面佈局，減少滾動需求',
                    'description': f'使用者需要滾動 {issue["count"]} 次才能找到目標，顯示重要資訊可能被隱藏。',
                    'recommendations': [
                        '將關鍵操作按鈕（加入購物車、購買）置於首屏可見範圍',
                        '使用「置頂」或「浮動」按鈕設計',
                        '優化商品頁面結構，將價格和購買按鈕放在更顯眼位置',
                        '考慮使用「回到頂部」快速導航按鈕'
                    ],
                    'persona_specific': f'{self.persona.persona_type} 類型使用者期望快速找到目標'
                })

            elif issue['type'] == 'frequent_backtracking':
                recs.append({
                    'category': 'Navigation Flow',
                    'priority': 'HIGH',
                    'title': '改善導航流程，減少返回操作',
                    'description': f'使用者頻繁返回上一頁（{issue["count"]} 次），顯示流程不順暢。',
                    'recommendations': [
                        '檢視資訊架構，確保使用者能在當前頁面完成任務',
                        '加入「麵包屑」導航，清楚顯示當前位置',
                        '提供相關推薦或連結，減少返回需求',
                        '確保所有必要資訊都在同一頁面可見'
                    ],
                    'persona_specific': '頻繁返回表示使用者迷失或資訊不完整'
                })

        return recs

    def _prioritize_by_persona(self, recommendations: List[Dict]) -> List[str]:
        """根據 persona 特徵排序優先行動"""
        priorities = []

        high_priority_recs = [r for r in recommendations if r.get('priority') == 'HIGH']

        if self.persona.persona_type == 'efficiency_oriented':
            priorities.append('🎯 效率型使用者最需要：立即、明確的操作回饋')
            for rec in high_priority_recs:
                if 'feedback' in rec.get('category', '').lower():
                    priorities.append(f"   → {rec['title']}")

        elif self.persona.persona_type == 'cautious_verifier':
            priorities.append('🎯 謹慎型使用者最需要：詳細、可驗證的資訊')
            for rec in high_priority_recs:
                if 'detail' in rec.get('category', '').lower() or 'clarity' in rec.get('category', '').lower():
                    priorities.append(f"   → {rec['title']}")

        return priorities


def generate_report(recommendations: Dict, output_file: str):
    """產生易讀的 Markdown 報告"""
    persona = recommendations['persona_info']

    report = f"""# UX 分析報告

## Persona 資訊
- **姓名**: {persona['name']}
- **類型**: {persona['type']}
- **關鍵特徵**:
  - 風險感知: {persona['key_traits']['risk_perception']}
  - 自我效能: {persona['key_traits']['self_efficacy']}
  - 工作記憶: {persona['key_traits']['working_memory']}
  - 任務策略: {persona['key_traits']['strategy']}

## 測試指標
- 總操作次數: {recommendations['task_metrics']['total_actions']}
- 總耗時: {recommendations['task_metrics']['total_time_ms'] / 1000:.2f} 秒
- 操作頻率: {recommendations['task_metrics']['actions_per_second']:.2f} 次/秒

## 發現的 UX 問題
"""

    for i, issue in enumerate(recommendations['detected_issues'], 1):
        report += f"\n### 問題 {i}: {issue.get('type', 'Unknown')}\n"
        report += f"- **嚴重程度**: {issue.get('severity', 'Unknown').upper()}\n"
        report += f"- **說明**: {issue.get('description', 'N/A')}\n"
        if 'repeat_count' in issue:
            report += f"- **重複次數**: {issue['repeat_count']}\n"

    report += "\n## 針對此 Persona 的改善建議\n"

    for i, rec in enumerate(recommendations['recommendations'], 1):
        report += f"\n### 建議 {i}: {rec['title']}\n"
        report += f"- **類別**: {rec['category']}\n"
        report += f"- **優先級**: {rec['priority']}\n"
        report += f"- **情境**: {rec['description']}\n"
        report += f"- **Persona 特定考量**: {rec.get('persona_specific', 'N/A')}\n"
        report += "\n**具體建議**:\n"
        for suggestion in rec.get('recommendations', []):
            report += f"  - {suggestion}\n"

    report += "\n## 優先行動項目\n"
    for action in recommendations['priority_actions']:
        report += f"{action}\n"

    report += f"\n---\n*報告產生時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

    # 寫入檔案
    Path(output_file).write_text(report, encoding='utf-8')
    print(f"\n✅ UX 分析報告已產生: {output_file}")

    return report


def main():
    parser = argparse.ArgumentParser(description='分析測試結果並產生 UX 建議')
    parser.add_argument('--run-dir', required=True, help='測試結果目錄 (例如: runs/2026-01-01_16-26-27_f19e)')
    parser.add_argument('--persona', required=True, help='Persona 檔案路徑')
    parser.add_argument('--output', help='輸出報告檔案路徑 (預設: run-dir/ux_analysis.md)')

    args = parser.parse_args()

    run_dir = Path(args.run_dir)
    memory_trace_file = run_dir / 'memory_trace.json'

    if not memory_trace_file.exists():
        print(f"❌ 找不到 memory_trace.json: {memory_trace_file}")
        return

    if not Path(args.persona).exists():
        print(f"❌ 找不到 persona 檔案: {args.persona}")
        return

    print(f"📊 開始分析測試結果...")
    print(f"   測試目錄: {run_dir}")
    print(f"   Persona: {args.persona}")

    # 讀取資料
    with open(memory_trace_file, 'r', encoding='utf-8') as f:
        memory_trace = json.load(f)

    # 建立分析器
    persona = PersonaProfile(args.persona)
    print(f"\n👤 Persona: {persona.name} ({persona.persona_type})")

    behavior = BehaviorAnalyzer(memory_trace)
    print(f"📈 分析 {len(behavior.actions)} 個動作, {len(behavior.reflections)} 個反思")

    # 產生建議
    generator = UXRecommendationGenerator(persona, behavior)
    recommendations = generator.generate_recommendations()

    # 產生報告
    output_file = args.output or str(run_dir / 'ux_analysis.md')
    report = generate_report(recommendations, output_file)

    # 同時儲存 JSON 格式
    json_output = str(run_dir / 'ux_analysis.json')
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(recommendations, f, ensure_ascii=False, indent=2)
    print(f"✅ JSON 資料已儲存: {json_output}")

    # 在終端顯示摘要
    print("\n" + "="*60)
    print("UX 分析摘要")
    print("="*60)
    print(f"\n發現 {len(recommendations['detected_issues'])} 個 UX 問題")
    print(f"產生 {len(recommendations['recommendations'])} 項改善建議\n")

    if recommendations['priority_actions']:
        print("🎯 優先行動項目:")
        for action in recommendations['priority_actions']:
            print(f"  {action}")

    print(f"\n📄 完整報告請見: {output_file}")


if __name__ == '__main__':
    main()
