"""予算に応じたギフト提案ツール。"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import re
from .base import BaseTool
import pandas as pd


class GiftRecommendationTool(BaseTool):
    """予算に応じたギフト提案を行うツール。

    麻布台ヒルズ内の店舗から、指定された予算に適したギフトアイテムを提案する。
    """

    @property
    def name(self) -> str:
        return "gift_recommendation"

    @property
    def description(self) -> str:
        return "予算に応じて麻布台ヒルズ内で購入可能なギフトを提案します。価格帯、受取人の属性、シーンに応じた商品やサービスを推奨します。"

    def __init__(self) -> None:
        super().__init__()

        # ギフトカテゴリー別の価格帯と店舗マッピング
        self.gift_categories = {
            "グルメ・スイーツ": {
                "低予算": (1000, 3000, [
                    "手土産用のクッキーやマカロン",
                    "コーヒー豆やティーバッグセット",
                    "プチケーキや焼き菓子",
                    "チョコレート詰め合わせ"
                ]),
                "中予算": (3000, 8000, [
                    "高級洋菓子セット",
                    "ワインやシャンパン",
                    "グルメ弁当やオードブル",
                    "プレミアムコーヒーセット"
                ]),
                "高予算": (8000, 20000, [
                    "高級レストランのディナーコース券",
                    "プレミアムワインセット",
                    "特別な記念日ケーキ",
                    "グルメギフトカード"
                ])
            },
            "ファッション・アクセサリー": {
                "低予算": (2000, 5000, [
                    "ハンドタオルやハンカチ",
                    "アクセサリー小物",
                    "コスメティック用品",
                    "スカーフやストール"
                ]),
                "中予算": (5000, 12000, [
                    "革小物（財布、キーケース）",
                    "ジュエリーアクセサリー",
                    "ブランド化粧品セット",
                    "バッグや小物入れ"
                ]),
                "高予算": (12000, 30000, [
                    "高級ブランド小物",
                    "プレミアムジュエリー",
                    "デザイナーアクセサリー",
                    "特別オーダー商品"
                ])
            },
            "体験・サービス": {
                "低予算": (3000, 6000, [
                    "カフェやレストランの食事券",
                    "書籍や雑貨",
                    "スパやエステの体験券（短時間）",
                    "映画鑑賞券"
                ]),
                "中予算": (6000, 15000, [
                    "高級レストランのランチコース",
                    "スパ・マッサージ体験",
                    "ワークショップ参加券",
                    "特別イベント招待券"
                ]),
                "高予算": (15000, 40000, [
                    "プレミアムディナー体験",
                    "スペシャルスパパッケージ",
                    "プライベートショッピング体験",
                    "VIP体験プログラム"
                ])
            }
        }

    def _determine_budget_category(self, budget: int) -> str:
        """予算金額からカテゴリーを判定する。"""
        if budget <= 5000:
            return "低予算"
        elif budget <= 15000:
            return "中予算"
        else:
            return "高予算"

    def _extract_budget(self, query: str) -> Optional[int]:
        """クエリから予算金額を抽出する。"""
        # 数字と円を含むパターンを検索（より具体的なパターンを先に配置）
        patterns = [
            r'(\d+,\d+)円',   # カンマ付き数字（例：10,000円）
            r'(\d+)万円',     # 万円（例：1万円）
            r'(\d+)千円',     # 千円（例：5千円）
            r'予算.*?(\d+)円', # 予算〇円
            r'(\d+)円で',     # 「〇円で」パターン
            r'(\d+)円の',     # 「〇円の」パターン
            r'(\d+)円',       # 基本的な数字円パターン（最後に配置）
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                number_str = match.group(1)
                if '千円' in pattern:
                    return int(number_str) * 1000
                elif '万円' in pattern:
                    return int(number_str) * 10000
                elif ',' in number_str:
                    # カンマを除去して数値化
                    return int(number_str.replace(',', ''))
                else:
                    return int(number_str)
        return None

    def _get_recipient_type(self, query: str) -> str:
        """受取人のタイプを判定する。"""
        query_lower = query.lower()

        if any(word in query for word in ['彼女', '女性', 'レディース', '奥さん', '妻', 'ガールフレンド']):
            return "女性"
        elif any(word in query for word in ['彼氏', '男性', 'メンズ', '旦那', '夫', 'ボーイフレンド']):
            return "男性"
        elif any(word in query for word in ['友達', '友人', '同僚', '上司', '部下']):
            return "友人・同僚"
        elif any(word in query for word in ['母', 'お母さん', '父', 'お父さん', '両親', '親']):
            return "家族"
        elif any(word in query for word in ['子供', 'こども', '息子', '娘']):
            return "子供"
        else:
            return "一般"

    def _get_occasion(self, query: str) -> str:
        """贈答の機会・シーンを判定する。"""
        if any(word in query for word in ['誕生日', 'バースデー', 'birthday']):
            return "誕生日"
        elif any(word in query for word in ['記念日', 'アニバーサリー', '結婚記念日']):
            return "記念日"
        elif any(word in query for word in ['クリスマス', 'Xmas', 'Christmas']):
            return "クリスマス"
        elif any(word in query for word in ['バレンタイン', 'Valentine', 'ホワイトデー']):
            return "バレンタイン・ホワイトデー"
        elif any(word in query for word in ['お礼', '感謝', 'ありがとう', 'お世話']):
            return "お礼・感謝"
        elif any(word in query for word in ['手土産', 'おみやげ', 'お土産']):
            return "手土産"
        else:
            return "一般"

    def _load_narrative_data(self) -> Optional[Dict[str, Any]]:
        """ナラティブデータを読み込む。"""
        try:
            from pathlib import Path
            import json

            project_root = Path(__file__).parent.parent.parent.parent
            narrative_file = project_root / "input" / "narrative_data.json"

            if narrative_file.exists():
                with open(narrative_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            return None
        return None

    def execute(self, query: str, user_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """ギフト提案を実行する。

        Args:
            query: ユーザーからの質問や要求
            user_context: ユーザーの分析結果やコンテキスト

        Returns:
            ギフト提案結果を含む辞書
        """
        try:
            # ナラティブデータを取得
            narrative_data = self._load_narrative_data()
            # 予算を抽出
            budget = self._extract_budget(query)
            if not budget:
                return {
                    "success": False,
                    "message": "予算が明確でありません。「〇〇円で」「予算〇〇円」のように具体的な金額を教えてください。",
                    "suggestions": [
                        "例：「10,000円で彼女にプレゼントを考えています」",
                        "例：「予算5,000円で上司への手土産を探しています」"
                    ]
                }

            # 受取人とシーンを分析
            recipient_type = self._get_recipient_type(query)
            occasion = self._get_occasion(query)
            budget_category = self._determine_budget_category(budget)

            # ギフト提案を生成
            recommendations = []

            for category, budget_info in self.gift_categories.items():
                if budget_category in budget_info:
                    min_price, max_price, items = budget_info[budget_category]

                    # 予算範囲内かチェック
                    if min_price <= budget <= max_price or budget >= min_price:
                        for item in items:
                            recommendations.append({
                                "category": category,
                                "item": item,
                                "estimated_price": f"{min_price:,}円 - {min(max_price, budget):,}円",
                                "suitable_for": recipient_type,
                                "occasion": occasion
                            })

            # ナラティブデータとユーザー分析結果を活用
            personalized_notes = []

            # ナラティブデータに基づく提案
            if narrative_data:
                age = narrative_data.get("age")
                gender = narrative_data.get("gender")

                if age:
                    if age < 30:
                        personalized_notes.append("若い世代向けのトレンドアイテムやカジュアルなギフトがおすすめです")
                    elif age >= 50:
                        personalized_notes.append("上質で落ち着いたアイテムや体験型のギフトがおすすめです")
                    else:
                        personalized_notes.append("幅広い年代に喜ばれる上品なアイテムがおすすめです")

                if gender == "女性":
                    personalized_notes.append("美容・コスメ関連アイテムやアクセサリーも人気です")
                elif gender == "男性":
                    personalized_notes.append("実用的なアイテムやグルメ関連のギフトが好まれる傾向があります")

            # セッション分析結果を活用
            if user_context and user_context.get("interests"):
                interests = user_context["interests"]
                if "食事" in interests or "グルメ" in interests:
                    personalized_notes.append("グルメ・スイーツ系のギフトが特におすすめです")
                if "ファッション" in interests or "買い物" in interests:
                    personalized_notes.append("ファッション・アクセサリー系のアイテムも検討してみてください")

            # 結果をまとめる
            result = {
                "success": True,
                "budget": f"{budget:,}円",
                "budget_category": budget_category,
                "recipient_type": recipient_type,
                "occasion": occasion,
                "recommendations": recommendations[:8],  # 上位8件
                "personalized_notes": personalized_notes,
                "shopping_locations": [
                    "麻布台ヒルズ ガーデンプラザ B1F-3F（ショッピング）",
                    "麻布台ヒルズ タワープラザ 1F-2F（レストラン・カフェ）",
                    "麻布台ヒルズ ガーデンプラザ 4F（レストラン）"
                ],
                "additional_tips": [
                    f"{budget_category}の予算帯では、{recipient_type}向けの{occasion}ギフトとして上記のようなアイテムがおすすめです",
                    "営業時間や在庫状況は事前に店舗へ確認することをお勧めします",
                    "特別包装やギフトカードサービスの有無も店舗へお問い合わせください"
                ]
            }

            return result

        except Exception as e:
            return {
                "success": False,
                "error": f"ギフト提案の処理中にエラーが発生しました: {str(e)}",
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
                            "description": "ギフトに関する質問や要求（予算、受取人、シーンを含む）"
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
