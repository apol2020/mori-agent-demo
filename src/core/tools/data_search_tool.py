"""店舗・イベント・ナラティブデータを検索するツール。"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.tools.base import BaseTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataSearchTool(BaseTool):
    """inputフォルダ内のデータを検索するツール。"""

    def __init__(self) -> None:
        """データ検索ツールを初期化する。"""
        # プロジェクトルートからinputフォルダのパスを設定
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.input_dir = self.project_root / "input"

        # データファイルのパス
        self.events_file = self.input_dir / "events.csv"
        self.stores_file = self.input_dir / "filtered_store_data_20251007_141616.csv"
        self.narrative_file = self.input_dir / "narrative_data.json"

    @property
    def name(self) -> str:
        return "search_data"

    @property
    def description(self) -> str:
        return """[DataSearchSQL] AIエージェントコンシェルジュツール

        麻布台ヒルズの店舗・イベント・ナラティブデータに対する絞り込み検索を実行します。
        SQLを直接書く必要はなく、パラメータ指定で簡単に検索できます。

        ⚠️ 制限事項:
        - 全データ取得は推奨されません
        - 最大100件まで取得可能（limit指定推奨）
        - データ型に応じたフィルタリング条件を指定
        - 日本語カラム名は直接指定可能

        ----------------------------
        📊 データセット概要
        ----------------------------
        • 店舗データ: 4件（麻布台ヒルズ関連店舗）
        • イベントデータ: 32件（関連イベント情報）
        • 主要カラム数: 11カラム（店舗）、12カラム（イベント）

        🔑 主要カラム分類:
        • 識別: store_id, event_name
        • 基本情報: store_name, description, category, location
        • 営業情報: opening_hours, irregular_closures
        • 連絡先: phone, email, address
        • イベント詳細: date_time, capacity, cost, registration_required
        • ステータス: extraction_status, target_audience

        ----------------------------
        💡 使用例
        ----------------------------
        1. 店舗IDで直接検索（推奨）:
           store_id="STR-0001"
           ※ 店舗情報と関連イベントを一括取得

        2. カテゴリ別店舗検索:
           data_type="stores"
           column_filters={"category": "retail"}

        3. 電話予約可能な店舗:
           data_type="stores"
           column_filters={"phone": {"operator": "not_null"}}
           sort_by="store_name"

        4. イベント名での部分一致検索:
           data_type="events"
           column_filters={"event_name": {"operator": "contains", "value": "Market"}}

        5. 複合検索（店舗名とカテゴリ）:
           query="ヒルズ"
           data_type="stores"
           column_filters={"category": "cafe"}

        6. ページネーション対応検索:
           data_type="events"
           sort_by="event_name"
           limit=5
           offset=0

        ----------------------------
        🎯 推奨SELECT句（用途別）
        ----------------------------
        • 店舗基本情報: store_name, category, phone, address
        • イベント概要: event_name, description, date_time, location
        • 営業時間確認: store_name, opening_hours, irregular_closures
        • 連絡先一覧: store_name, phone, email, address

        利用可能な演算子: equals, contains, like, not_null, is_null, gt, lt, gte, lte, in
        """

    def execute(self, **kwargs: Any) -> Any:
        """データを検索して結果を返す。

        Args:
            query (str, optional): 検索クエリ（店舗名、イベント名、説明文などで検索）
            store_id (str, optional): 店舗ID（STR-0001形式）で直接検索
            data_type (str, optional): データタイプを指定（"stores", "events", "narrative", "all"）
            category (str, optional): カテゴリで絞り込み（店舗データの場合）
            column_filters (dict, optional): カラム別の詳細検索条件
            sort_by (str, optional): ソート対象カラム
            sort_order (str, optional): ソート順（"asc", "desc"）
            limit (int, optional): 取得件数制限
            offset (int, optional): オフセット（ページネーション用）

        Returns:
            検索結果のリスト
        """
        # 既存パラメータ（後方互換性）
        query = kwargs.get("query", "")
        store_id = kwargs.get("store_id", "")
        data_type = kwargs.get("data_type", "all")
        category = kwargs.get("category", "")

        # 新しいSQLライクパラメータ
        column_filters = kwargs.get("column_filters", {})
        sort_by = kwargs.get("sort_by", "")
        sort_order = kwargs.get("sort_order", "asc").lower()
        limit = kwargs.get("limit", None)
        offset = kwargs.get("offset", 0)

        try:
            results = {}

            # 店舗IDが指定された場合は優先して処理
            if store_id:
                store_data = self._get_store_by_id(store_id)
                if store_data:
                    results["stores"] = [store_data]
                    # 関連イベントも取得
                    if data_type in ["events", "all"]:
                        related_events = self._get_events_by_store_id(store_id, store_data)
                        if related_events:
                            results["events"] = related_events
                    return results
                else:
                    return {"error": f"店舗ID「{store_id}」が見つかりませんでした"}

            if data_type in ["stores", "all"]:
                stores_data = self._search_stores(query, category, column_filters)
                if stores_data:
                    # ソート適用
                    stores_data = self._apply_sorting(stores_data, sort_by, sort_order)
                    # ページネーション適用
                    stores_data = self._apply_pagination(stores_data, limit, offset)
                    results["stores"] = stores_data

            if data_type in ["events", "all"]:
                events_data = self._search_events(query, column_filters)
                if events_data:
                    # ソート適用
                    events_data = self._apply_sorting(events_data, sort_by, sort_order)
                    # ページネーション適用
                    events_data = self._apply_pagination(events_data, limit, offset)
                    results["events"] = events_data

            if data_type in ["narrative", "all"]:
                narrative_data = self._get_narrative_data()
                if narrative_data:
                    # ナラティブデータを使いやすい形で提供
                    enhanced_narrative = {
                        "user_profile": narrative_data,
                        "recommendations": self._generate_narrative_based_recommendations(narrative_data)
                    }
                    results["narrative"] = enhanced_narrative

            return results

        except Exception as e:
            logger.error(f"Error searching data: {e}")
            return {"error": f"データ検索中にエラーが発生しました: {str(e)}"}

    def _get_store_by_id(self, store_id: str) -> Optional[Dict[str, Any]]:
        """店舗IDで店舗データを取得する。

        Args:
            store_id: 店舗ID（STR-0001形式）

        Returns:
            店舗データまたはNone
        """
        if not self.stores_file.exists():
            return None

        try:
            with open(self.stores_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('store_id', '').upper() == store_id.upper():
                        return row
            return None
        except Exception as e:
            logger.error(f"Error getting store by ID: {e}")
            return None

    def _get_events_by_store_id(self, store_id: str, store_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """店舗IDに関連するイベントを取得する。

        Args:
            store_id: 店舗ID
            store_data: 店舗データ（店舗名や電話番号での照合用）

        Returns:
            関連イベントのリスト
        """
        if not self.events_file.exists():
            return []

        try:
            results = []
            store_name = store_data.get('store_name', '')
            store_phone = store_data.get('phone', '')

            with open(self.events_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 店舗名での照合
                    location = row.get('location', '')
                    if store_name and store_name in location:
                        results.append(row)
                        continue

                    # 電話番号での照合
                    contact_info = row.get('contact_info', '')
                    if store_phone and store_phone in contact_info:
                        results.append(row)
                        continue

            return results
        except Exception as e:
            logger.error(f"Error getting events by store ID: {e}")
            return []

    def _search_stores(self, query: str, category: str = "", column_filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """店舗データを検索する。"""
        if not self.stores_file.exists():
            return []

        try:
            results = []
            column_filters = column_filters or {}

            with open(self.stores_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 従来のカテゴリフィルター（後方互換性）
                    if category and row.get('category', '').lower() != category.lower():
                        continue

                    # 新しいカラムフィルタリング
                    if not self._apply_column_filters(row, column_filters):
                        continue

                    # 従来のクエリ検索（後方互換性）
                    if query:
                        searchable_text = f"{row.get('store_name', '')} {row.get('description', '')} {row.get('address', '')}".lower()

                        # クエリをスペースで分割してキーワードリストにする
                        keywords = [kw.strip() for kw in query.lower().split() if kw.strip()]

                        # いずれかのキーワードがマッチすれば結果に含める
                        if not keywords or any(keyword in searchable_text for keyword in keywords):
                            results.append(row)
                            continue

                        # 何もマッチしなければスキップ
                        continue

                    results.append(row)

            return results
        except Exception as e:
            logger.error(f"Error reading stores file: {e}")
            return []

    def _search_events(self, query: str, column_filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """イベントデータを検索する。"""
        if not self.events_file.exists():
            return []

        try:
            results = []
            column_filters = column_filters or {}

            with open(self.events_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 新しいカラムフィルタリング
                    if not self._apply_column_filters(row, column_filters):
                        continue

                    # 従来のクエリ検索（後方互換性）
                    if query:
                        searchable_text = f"{row.get('event_name', '')} {row.get('description', '')} {row.get('location', '')}".lower()

                        # クエリをスペースで分割してキーワードリストにする
                        keywords = [kw.strip() for kw in query.lower().split() if kw.strip()]

                        # いずれかのキーワードがマッチすれば結果に含める
                        if not keywords or any(keyword in searchable_text for keyword in keywords):
                            results.append(row)
                            continue

                        # 何もマッチしなければスキップ
                        continue

                    results.append(row)

            return results
        except Exception as e:
            logger.error(f"Error reading events file: {e}")
            return []

    def _get_narrative_data(self) -> Optional[Dict[str, Any]]:
        """ナラティブデータを取得する。"""
        if not self.narrative_file.exists():
            return None

        try:
            with open(self.narrative_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading narrative file: {e}")
            return None

    def _generate_narrative_based_recommendations(self, narrative_data: Dict[str, Any]) -> Dict[str, Any]:
        """ナラティブデータに基づく推奨事項を生成する。"""
        recommendations = {
            "store_categories": [],
            "activity_suggestions": [],
            "time_preferences": [],
            "gift_preferences": []
        }

        age = narrative_data.get("age")
        gender = narrative_data.get("gender")

        # 年齢に基づく推奨
        if age:
            if age < 30:
                recommendations["store_categories"].extend(["カジュアルダイニング", "トレンドショップ", "カフェ"])
                recommendations["activity_suggestions"].extend(["写真撮影スポット巡り", "新しいお店の発見"])
                recommendations["gift_preferences"].extend(["トレンドアイテム", "インスタ映えするグッズ"])
            elif age >= 50:
                recommendations["store_categories"].extend(["高級レストラン", "伝統工芸品店", "スパ・エステ"])
                recommendations["activity_suggestions"].extend(["ゆったりとした食事", "文化的な体験"])
                recommendations["gift_preferences"].extend(["上質なアイテム", "体験型ギフト"])
            else:
                recommendations["store_categories"].extend(["ビジネスカジュアル店舗", "ファインダイニング"])
                recommendations["activity_suggestions"].extend(["効率的なショッピング", "質の高い食事体験"])

        # 性別に基づく推奨
        if gender == "女性":
            recommendations["store_categories"].extend(["コスメティック", "ジュエリー", "ファッション"])
            recommendations["activity_suggestions"].extend(["美容関連サービス", "アクセサリーショッピング"])
            recommendations["gift_preferences"].extend(["美容アイテム", "アクセサリー", "スイーツ"])
        elif gender == "男性":
            recommendations["store_categories"].extend(["メンズファッション", "ガジェット", "グルメ"])
            recommendations["activity_suggestions"].extend(["実用的なショッピング", "グルメ体験"])
            recommendations["gift_preferences"].extend(["実用アイテム", "グルメギフト", "体験券"])

        return recommendations

    def _apply_column_filters(self, row: Dict[str, Any], column_filters: Dict[str, Any]) -> bool:
        """カラム別フィルタリングを適用する。

        Args:
            row: データ行
            column_filters: カラムフィルタ設定

        Returns:
            フィルタ条件に合致するかどうか
        """
        if not column_filters:
            return True

        for column, filter_config in column_filters.items():
            column_value = row.get(column, "")

            # 簡潔記法（文字列直接指定）
            if isinstance(filter_config, str):
                if column_value.lower() != filter_config.lower():
                    return False
            # 明示記法（辞書指定）
            elif isinstance(filter_config, dict):
                operator = filter_config.get("operator", "equals")
                value = filter_config.get("value", "")

                if not self._evaluate_condition(column_value, operator, value):
                    return False

        return True

    def _evaluate_condition(self, column_value: str, operator: str, target_value: Any) -> bool:
        """条件評価を行う。

        Args:
            column_value: カラムの値
            operator: 演算子
            target_value: 比較対象の値

        Returns:
            条件に合致するかどうか
        """
        column_str = str(column_value).lower()
        target_str = str(target_value).lower()

        if operator == "equals":
            return column_str == target_str
        elif operator == "contains":
            return target_str in column_str
        elif operator == "like":
            # 簡易的なワイルドカード対応
            import re
            pattern = target_str.replace("%", ".*").replace("_", ".")
            return bool(re.search(pattern, column_str))
        elif operator == "not_null":
            return column_value is not None and column_value != ""
        elif operator == "is_null":
            return column_value is None or column_value == ""
        elif operator == "gt":
            try:
                return float(column_value) > float(target_value)
            except (ValueError, TypeError):
                return False
        elif operator == "lt":
            try:
                return float(column_value) < float(target_value)
            except (ValueError, TypeError):
                return False
        elif operator == "gte":
            try:
                return float(column_value) >= float(target_value)
            except (ValueError, TypeError):
                return False
        elif operator == "lte":
            try:
                return float(column_value) <= float(target_value)
            except (ValueError, TypeError):
                return False
        elif operator == "in":
            if isinstance(target_value, list):
                return column_str in [str(v).lower() for v in target_value]
            return False
        else:
            # デフォルトは equals
            return column_str == target_str

    def _apply_sorting(self, data: List[Dict[str, Any]], sort_by: str, sort_order: str) -> List[Dict[str, Any]]:
        """データのソートを適用する。

        Args:
            data: ソート対象のデータ
            sort_by: ソート対象カラム
            sort_order: ソート順（"asc", "desc"）

        Returns:
            ソート済みのデータ
        """
        if not sort_by or not data:
            return data

        reverse = sort_order == "desc"

        try:
            return sorted(data, key=lambda x: str(x.get(sort_by, "")), reverse=reverse)
        except Exception as e:
            logger.warning(f"Sorting failed: {e}")
            return data

    def _apply_pagination(self, data: List[Dict[str, Any]], limit: Optional[int], offset: int) -> List[Dict[str, Any]]:
        """ページネーションを適用する。

        Args:
            data: ページネーション対象のデータ
            limit: 取得件数制限
            offset: オフセット

        Returns:
            ページネーション適用後のデータ
        """
        if not data:
            return data

        start_idx = max(0, offset)

        if limit is None:
            return data[start_idx:]
        else:
            end_idx = start_idx + max(0, limit)
            return data[start_idx:end_idx]


class StoreInfoTool(BaseTool):
    """特定の店舗の詳細情報を取得するツール。"""

    def __init__(self) -> None:
        """店舗情報ツールを初期化する。"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.input_dir = self.project_root / "input"
        self.stores_file = self.input_dir / "filtered_store_data_20251007_141616.csv"

    @property
    def name(self) -> str:
        return "get_store_info"

    @property
    def description(self) -> str:
        return "店舗名または店舗ID（STR-0001形式）を指定して、その店舗の詳細情報（営業時間、連絡先、住所など）を取得する。店舗IDでの検索が優先される。"

    def execute(self, **kwargs: Any) -> Any:
        """店舗の詳細情報を取得する。

        Args:
            store_name (str, optional): 店舗名
            store_id (str, optional): 店舗ID（STR-0001形式）

        Returns:
            店舗の詳細情報
        """
        store_name = kwargs.get("store_name", "")
        store_id = kwargs.get("store_id", "")

        if not store_name and not store_id:
            return {"error": "店舗名または店舗IDを指定してください"}

        try:
            if not self.stores_file.exists():
                return {"error": "店舗データファイルが見つかりません"}

            with open(self.stores_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 店舗IDでの完全一致検索（優先）
                    if store_id and row.get('store_id', '').upper() == store_id.upper():
                        return row
                    # 店舗名での部分一致検索
                    if store_name and store_name.lower() in row.get('store_name', '').lower():
                        return row

            search_term = store_id if store_id else store_name
            return {"error": f"店舗「{search_term}」が見つかりませんでした"}

        except Exception as e:
            logger.error(f"Error getting store info: {e}")
            return {"error": f"店舗情報取得中にエラーが発生しました: {str(e)}"}


class StoreByIdTool(BaseTool):
    """店舗IDで店舗と関連イベントを一括取得する専用ツール。"""

    def __init__(self) -> None:
        """店舗ID検索ツールを初期化する。"""
        self.data_search_tool = DataSearchTool()

    @property
    def name(self) -> str:
        return "get_store_by_id"

    @property
    def description(self) -> str:
        return """店舗ID（STR-0001形式）を指定して、その店舗の詳細情報と関連イベントを一括取得する。
        最も効率的な店舗情報取得方法。店舗情報、関連イベント、営業時間、連絡先などを包括的に提供。"""

    def execute(self, **kwargs: Any) -> Any:
        """店舗IDで店舗と関連データを取得する。

        Args:
            store_id (str): 店舗ID（STR-0001形式）

        Returns:
            店舗情報と関連イベントの辞書
        """
        store_id = kwargs.get("store_id", "")

        if not store_id:
            return {"error": "店舗IDを指定してください（例: STR-0001）"}

        # DataSearchToolを使用してデータ取得
        result = self.data_search_tool.execute(store_id=store_id, data_type="all")

        # 結果を整理
        if "error" in result:
            return result

        return {
            "store_id": store_id,
            "store_info": result.get("stores", [{}])[0] if result.get("stores") else None,
            "related_events": result.get("events", []),
            "total_related_events": len(result.get("events", [])),
            "success": True
        }


class EventInfoTool(BaseTool):
    """特定のイベントの詳細情報を取得するツール。"""

    def __init__(self) -> None:
        """イベント情報ツールを初期化する。"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.input_dir = self.project_root / "input"
        self.events_file = self.input_dir / "events.csv"

    @property
    def name(self) -> str:
        return "get_event_info"

    @property
    def description(self) -> str:
        return "イベント名を指定して、そのイベントの詳細情報（日時、場所、料金など）を取得する。"

    def execute(self, **kwargs: Any) -> Any:
        """イベントの詳細情報を取得する。

        Args:
            event_name (str): イベント名

        Returns:
            イベントの詳細情報
        """
        event_name = kwargs.get("event_name", "")

        if not event_name:
            return {"error": "イベント名を指定してください"}

        try:
            if not self.events_file.exists():
                return {"error": "イベントデータファイルが見つかりません"}

            with open(self.events_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if event_name.lower() in row.get('event_name', '').lower():
                        return row

            return {"error": f"イベント「{event_name}」が見つかりませんでした"}

        except Exception as e:
            logger.error(f"Error getting event info: {e}")
            return {"error": f"イベント情報取得中にエラーが発生しました: {str(e)}"}
