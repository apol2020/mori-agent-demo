"""ユーザーの趣味嗜好・興味分析ツール。"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from src.core.tools.base import BaseTool


class UserInterestAnalysisTool(BaseTool):
    """チャット履歴からユーザーの趣味嗜好・興味を分析するツール。"""

    def __init__(self):
        # セッション内の分析データを保持
        self.session_analysis = {
            "interests": {},
            "preferences": {},
            "visit_patterns": {},
            "behavior_patterns": {},
            "last_updated": None
        }

    @property
    def name(self) -> str:
        """ツール名。"""
        return "user_interest_analysis"

    @property
    def description(self) -> str:
        """ツールの説明。"""
        return "チャット履歴からユーザーの趣味嗜好・興味・行動パターンを分析します"

    def _extract_interests_from_message(self, message: str) -> Dict[str, Any]:
        """メッセージから興味関心を抽出する。"""
        interests = {}
        
        # 店舗カテゴリのキーワードマッピング
        category_keywords = {
            "飲食": ["レストラン", "カフェ", "食事", "ランチ", "ディナー", "食べる", "グルメ", 
                    "和食", "洋食", "中華", "イタリアン", "フレンチ", "寿司", "ラーメン", 
                    "コーヒー", "デザート", "スイーツ", "お酒", "バー", "居酒屋", "テイクアウト"],
            "ショッピング": ["買い物", "服", "ファッション", "アパレル", "雑貨", "お土産", 
                           "ブランド", "購入", "買う", "ショップ", "商品", "セール", "プレゼント"],
            "エンターテイメント": ["映画", "劇場", "コンサート", "イベント", "展示", "アート", 
                                "文化", "エンタメ", "観光", "散歩", "写真", "体験"],
            "健康・美容": ["スパ", "エステ", "マッサージ", "美容", "健康", "リラックス", 
                         "フィットネス", "ジム", "ヨガ", "サロン"],
            "ビジネス": ["会議", "オフィス", "仕事", "ビジネス", "商談", "ワーク", 
                       "打ち合わせ", "相談", "コワーキング"],
            "家族・子供": ["子供", "キッズ", "ファミリー", "家族", "親子", "赤ちゃん", 
                         "育児", "遊び場", "子連れ"]
        }
        
        # 時間帯の好み
        time_keywords = {
            "朝": ["朝", "モーニング", "9時", "10時", "11時"],
            "昼": ["昼", "ランチ", "12時", "13時", "14時", "15時"],
            "夕方": ["夕方", "16時", "17時", "18時"],
            "夜": ["夜", "ディナー", "19時", "20時", "21時", "22時"]
        }
        
        message_lower = message.lower()
        
        # カテゴリ興味度を計算
        for category, keywords in category_keywords.items():
            count = sum(1 for keyword in keywords if keyword in message_lower)
            if count > 0:
                interests[f"category_{category}"] = count
        
        # 時間帯の好みを分析
        for time_period, keywords in time_keywords.items():
            count = sum(1 for keyword in keywords if keyword in message_lower)
            if count > 0:
                interests[f"time_{time_period}"] = count
        
        return interests

    def _analyze_visit_patterns(self, message: str) -> Dict[str, Any]:
        """訪問パターンや行動を分析する。"""
        patterns = {}
        
        # 頻度に関するキーワード
        frequency_keywords = {
            "高頻度": ["よく", "いつも", "毎日", "頻繁", "しょっちゅう"],
            "中頻度": ["時々", "たまに", "週末", "休日"],
            "低頻度": ["初めて", "久しぶり", "たまには"]
        }
        
        # 同行者パターン
        companion_keywords = {
            "一人": ["一人", "ひとり", "個人"],
            "友人": ["友達", "友人", "仲間"],
            "家族": ["家族", "子供", "親", "夫", "妻"],
            "恋人": ["彼氏", "彼女", "恋人", "カップル"],
            "同僚": ["同僚", "上司", "部下", "仕事"]
        }
        
        message_lower = message.lower()
        
        # 頻度パターンを分析
        for freq_type, keywords in frequency_keywords.items():
            count = sum(1 for keyword in keywords if keyword in message_lower)
            if count > 0:
                patterns[f"frequency_{freq_type}"] = count
        
        # 同行者パターンを分析
        for companion_type, keywords in companion_keywords.items():
            count = sum(1 for keyword in keywords if keyword in message_lower)
            if count > 0:
                patterns[f"companion_{companion_type}"] = count
        
        return patterns

    def execute(self, **kwargs) -> Dict[str, Any]:
        """チャット履歴を分析してユーザーの趣味嗜好を更新する。"""
        try:
            chat_history = kwargs.get("chat_history", [])
            
            if not chat_history:
                return {
                    "success": False,
                    "message": "分析するチャット履歴がありません"
                }
            
            # 新しい分析データを初期化
            new_interests = {}
            new_preferences = {}
            new_visit_patterns = {}
            new_behavior_patterns = {}
            
            # チャット履歴を分析
            for message in chat_history[-10:]:  # 直近10メッセージを分析
                if isinstance(message, dict) and message.get("role") == "user":
                    content = message.get("content", "")
                    
                    # 興味関心を抽出
                    interests = self._extract_interests_from_message(content)
                    for key, value in interests.items():
                        new_interests[key] = new_interests.get(key, 0) + value
                    
                    # 行動パターンを分析
                    patterns = self._analyze_visit_patterns(content)
                    for key, value in patterns.items():
                        new_behavior_patterns[key] = new_behavior_patterns.get(key, 0) + value
            
            # セッション分析データを更新
            self.session_analysis["interests"].update(new_interests)
            self.session_analysis["behavior_patterns"].update(new_behavior_patterns)
            self.session_analysis["last_updated"] = datetime.now().isoformat()
            
            # 上位の興味関心を抽出
            top_interests = sorted(
                self.session_analysis["interests"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:5]
            
            top_patterns = sorted(
                self.session_analysis["behavior_patterns"].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            analysis_result = {
                "primary_interests": dict(top_interests),
                "behavior_patterns": dict(top_patterns),
                "analysis_summary": self._generate_summary(top_interests, top_patterns)
            }
            
            return {
                "success": True,
                "analysis": analysis_result,
                "message": "ユーザー分析が完了しました"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "分析中にエラーが発生しました"
            }

    def _generate_summary(self, interests: List, patterns: List) -> str:
        """分析結果のサマリーを生成する。"""
        summary_parts = []
        
        if interests:
            interest_names = []
            for key, _ in interests:
                if key.startswith("category_"):
                    interest_names.append(key.replace("category_", ""))
                elif key.startswith("time_"):
                    interest_names.append(f"{key.replace('time_', '')}の時間帯")
            
            if interest_names:
                summary_parts.append(f"主な興味: {', '.join(interest_names[:3])}")
        
        if patterns:
            pattern_names = []
            for key, _ in patterns:
                if key.startswith("frequency_"):
                    pattern_names.append(f"{key.replace('frequency_', '')}利用者")
                elif key.startswith("companion_"):
                    pattern_names.append(f"{key.replace('companion_', '')}での来訪")
            
            if pattern_names:
                summary_parts.append(f"行動パターン: {', '.join(pattern_names[:2])}")
        
        return " | ".join(summary_parts) if summary_parts else "分析データが不十分です"

    def get_current_analysis(self) -> Dict[str, Any]:
        """現在の分析結果を取得する。"""
        return self.session_analysis.copy()