"""1日の活動計画提案ツール。"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re
from .base import BaseTool


class ActivityPlannerTool(BaseTool):
    """1日の過ごし方や活動計画を提案するツール。

    麻布台ヒルズ内外の施設やサービスを活用した1日のスケジュールを提案する。
    """

    @property
    def name(self) -> str:
        return "activity_planner"

    @property
    def description(self) -> str:
        return "1日の過ごし方や活動計画を提案します。時間帯、人数、興味・関心、予算に応じて麻布台ヒルズ内外の最適な活動スケジュールを作成します。"

    def __init__(self) -> None:
        super().__init__()

        # 時間帯別のおすすめ活動
        self.time_slot_activities = {
            "朝": {
                "早朝 (6:00-8:00)": [
                    "六本木ヒルズ周辺の朝散歩",
                    "麻布台ヒルズ周辺のジョギング",
                    "カフェでモーニング"
                ],
                "朝 (8:00-11:00)": [
                    "麻布台ヒルズのカフェで朝食",
                    "ベーカリーでパンとコーヒー",
                    "朝の読書タイム",
                    "展望台での景色鑑賞"
                ]
            },
            "日中": {
                "午前 (11:00-13:00)": [
                    "ショッピング（ファッション・雑貨）",
                    "アート・ギャラリー見学",
                    "書店での本探し",
                    "スパ・エステ体験"
                ],
                "昼 (13:00-15:00)": [
                    "レストランでランチ",
                    "カフェでお茶",
                    "デリでテイクアウト",
                    "屋外テラスでの食事"
                ],
                "午後 (15:00-17:00)": [
                    "続きのショッピング",
                    "カフェでのんびり",
                    "ワークショップ参加",
                    "友人との会話"
                ]
            },
            "夜": {
                "夕方 (17:00-19:00)": [
                    "夕日鑑賞",
                    "バーでカクテルタイム",
                    "軽い食事やスナック",
                    "展望エリアでの景色鑑賞"
                ],
                "夜 (19:00-22:00)": [
                    "レストランでディナー",
                    "バーでお酒",
                    "夜景鑑賞",
                    "エンターテイメント"
                ],
                "深夜 (22:00-24:00)": [
                    "バーでナイトキャップ",
                    "深夜カフェ",
                    "夜景撮影",
                    "静かな時間"
                ]
            }
        }

        # 人数別のおすすめ活動
        self.group_activities = {
            "一人": [
                "読書やカフェタイム",
                "ショッピング",
                "アート鑑賞",
                "スパ・エステ",
                "のんびり散歩"
            ],
            "カップル": [
                "ロマンチックディナー",
                "景色の良い場所でお茶",
                "ペアでスパ体験",
                "夜景鑑賞",
                "記念写真撮影"
            ],
            "友人": [
                "グループでランチ・ディナー",
                "ショッピング巡り",
                "カフェでおしゃべり",
                "バーで乾杯",
                "イベント参加"
            ],
            "家族": [
                "ファミリーレストラン",
                "子供向けエリア",
                "家族写真撮影",
                "みんなでショッピング",
                "カジュアルな食事"
            ]
        }

        # 予算帯別の活動
        self.budget_activities = {
            "節約": (0, 3000, [
                "公園での散歩",
                "無料イベント参加",
                "カフェでコーヒー",
                "景色鑑賞",
                "ウィンドウショッピング"
            ]),
            "標準": (3000, 10000, [
                "カジュアルレストラン",
                "カフェでのんびり",
                "映画鑑賞",
                "軽いショッピング",
                "体験イベント"
            ]),
            "贅沢": (10000, 30000, [
                "高級レストラン",
                "プレミアムスパ",
                "高級ブランドショッピング",
                "特別体験プログラム",
                "VIPサービス"
            ])
        }

    def _extract_time_preference(self, query: str) -> List[str]:
        """クエリから希望する時間帯を抽出する。"""
        time_preferences = []

        if any(word in query for word in ['朝', 'モーニング', '午前中', '早い時間']):
            time_preferences.append("朝")
        if any(word in query for word in ['昼', 'ランチ', '午後', 'お昼']):
            time_preferences.append("日中")
        if any(word in query for word in ['夜', 'ディナー', '夕方', '夜景', 'ナイト']):
            time_preferences.append("夜")
        if any(word in query for word in ['1日', '一日', '終日', '朝から夜', '朝から晩']):
            time_preferences = ["朝", "日中", "夜"]

        return time_preferences if time_preferences else ["日中"]

    def _extract_group_type(self, query: str) -> str:
        """同行者のタイプを判定する。"""
        if any(word in query for word in ['一人', 'ひとり', 'ソロ', '自分だけ']):
            return "一人"
        elif any(word in query for word in ['カップル', '彼女', '彼氏', '恋人', '二人']):
            return "カップル"
        elif any(word in query for word in ['友達', '友人', '仲間', 'みんな']):
            return "友人"
        elif any(word in query for word in ['家族', '子供', 'ファミリー', '親子']):
            return "家族"
        else:
            return "一人"

    def _extract_budget(self, query: str) -> Optional[int]:
        """クエリから予算を抽出する。"""
        patterns = [
            r'(\d+)円',
            r'(\d+),(\d+)円',
            r'予算.*?(\d+)円',
            r'(\d+)千円',
            r'(\d+)万円'
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                if '千円' in pattern:
                    return int(match.group(1)) * 1000
                elif '万円' in pattern:
                    return int(match.group(1)) * 10000
                elif ',' in pattern:
                    return int(match.group(1)) * 1000 + int(match.group(2))
                else:
                    return int(match.group(1))
        return None

    def _determine_budget_category(self, budget: Optional[int]) -> str:
        """予算からカテゴリーを判定する。"""
        if budget is None:
            return "標準"
        elif budget <= 3000:
            return "節約"
        elif budget <= 10000:
            return "標準"
        else:
            return "贅沢"

    def _extract_interests(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> List[str]:
        """興味・関心を抽出する。"""
        interests = []

        # クエリから直接抽出
        if any(word in query for word in ['食事', 'グルメ', 'レストラン', '食べる']):
            interests.append("グルメ")
        if any(word in query for word in ['買い物', 'ショッピング', '服', 'ファッション']):
            interests.append("ショッピング")
        if any(word in query for word in ['リラックス', 'のんびり', '癒し', 'スパ']):
            interests.append("リラクゼーション")
        if any(word in query for word in ['景色', '展望', '夜景', '写真']):
            interests.append("景色鑑賞")
        if any(word in query for word in ['アート', '文化', '芸術', '展示']):
            interests.append("アート・文化")

        # ユーザーコンテキストから抽出
        if user_context and user_context.get("interests"):
            interests.extend(user_context["interests"])

        return list(set(interests)) if interests else ["グルメ", "ショッピング"]

    def _create_schedule(self, time_preferences: List[str], group_type: str,
                        budget_category: str, interests: List[str]) -> List[Dict[str, Any]]:
        """スケジュールを作成する。"""
        schedule = []

        for time_period in time_preferences:
            if time_period in self.time_slot_activities:
                for time_slot, activities in self.time_slot_activities[time_period].items():
                    # 興味に基づいて活動を選択
                    selected_activities = []
                    for activity in activities:
                        if any(interest.lower() in activity.lower() for interest in interests):
                            selected_activities.append(activity)

                    # 興味マッチがない場合は一般的な活動を選択
                    if not selected_activities:
                        selected_activities = activities[:2]

                    schedule.append({
                        "time_slot": time_slot,
                        "activities": selected_activities[:3],  # 最大3つ
                        "group_suitability": self._get_group_suitability(selected_activities, group_type),
                        "budget_fit": budget_category
                    })

        return schedule

    def _get_group_suitability(self, activities: List[str], group_type: str) -> str:
        """活動がグループタイプに適しているかの評価。"""
        group_activities = self.group_activities.get(group_type, [])

        matches = 0
        for activity in activities:
            for group_activity in group_activities:
                if any(word in activity.lower() for word in group_activity.lower().split()):
                    matches += 1
                    break

        if matches >= len(activities) * 0.7:
            return "非常に適している"
        elif matches >= len(activities) * 0.4:
            return "適している"
        else:
            return "普通"

    def execute(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """活動計画を実行する。

        Args:
            query: ユーザーからの質問や要求
            user_context: ユーザーの分析結果やコンテキスト

        Returns:
            活動計画結果を含む辞書
        """
        try:
            # パラメータ抽出
            time_preferences = self._extract_time_preference(query)
            group_type = self._extract_group_type(query)
            budget = self._extract_budget(query)
            budget_category = self._determine_budget_category(budget)
            interests = self._extract_interests(query, user_context)

            # スケジュール作成
            schedule = self._create_schedule(time_preferences, group_type, budget_category, interests)

            # 特別な提案を追加
            special_recommendations = []
            if "グルメ" in interests:
                special_recommendations.append("麻布台ヒルズの展望レストランでの食事がおすすめです")
            if "ショッピング" in interests:
                special_recommendations.append("ガーデンプラザでのショッピングと休憩を組み合わせてみてください")
            if "リラクゼーション" in interests:
                special_recommendations.append("スパやエステでリフレッシュタイムを取り入れてみてください")

            # 結果をまとめる
            result = {
                "success": True,
                "plan_summary": {
                    "time_periods": time_preferences,
                    "group_type": group_type,
                    "budget_category": budget_category,
                    "budget": f"{budget:,}円" if budget else "指定なし",
                    "main_interests": interests
                },
                "detailed_schedule": schedule,
                "special_recommendations": special_recommendations,
                "practical_tips": [
                    "各店舗の営業時間は事前に確認することをお勧めします",
                    "混雑する時間帯を避けて余裕のあるスケジュールを心がけてください",
                    "天気によって屋外活動の調整も考慮してください",
                    "予算に応じて飲食店やサービスを選択してください"
                ],
                "location_info": {
                    "main_areas": [
                        "麻布台ヒルズ ガーデンプラザ（ショッピング・レストラン）",
                        "麻布台ヒルズ タワープラザ（レストラン・カフェ）",
                        "周辺エリア（六本木ヒルズ、アークヒルズ）"
                    ],
                    "transportation": "地下鉄各線「神谷町駅」「六本木一丁目駅」から徒歩圏内"
                }
            }

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"活動計画の作成中にエラーが発生しました: {str(e)}",
                "message": "申し訳ございません。しばらく時間をおいて再度お試しください。"
            }

    def get_schema(self) -> Dict[str, Any]:
        """ツールのスキーマを取得する。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "1日の過ごし方や活動計画に関する質問や要求"
                        },
                        "user_context": {
                            "type": "object",
                            "description": "ユーザーの分析結果やコンテキスト情報",
                            "properties": {
                                "interests": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "description": "ユーザーの興味・関心"
                                }
                            }
                        }
                    },
                    "required": ["query"]
                }
            }
        }
