"""店舗・イベント・ナラティブデータを検索するツール。"""

import csv
import json
import os
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
        self.stores_file = self.input_dir / "filtered_store_data_20250926_052949.csv"
        self.narrative_file = self.input_dir / "narrative_data.json"

    @property
    def name(self) -> str:
        return "search_data"

    @property
    def description(self) -> str:
        return "店舗データ、イベントデータ、ナラティブデータを検索する。検索キーワードやカテゴリを指定して関連情報を取得できる。"

    def execute(self, **kwargs: Any) -> Any:
        """データを検索して結果を返す。

        Args:
            query (str, optional): 検索クエリ（店舗名、イベント名、説明文などで検索）
            data_type (str, optional): データタイプを指定（"stores", "events", "narrative", "all"）
            category (str, optional): カテゴリで絞り込み（店舗データの場合）

        Returns:
            検索結果のリスト
        """
        query = kwargs.get("query", "")
        data_type = kwargs.get("data_type", "all")
        category = kwargs.get("category", "")

        try:
            results = {}

            if data_type in ["stores", "all"]:
                stores_data = self._search_stores(query, category)
                if stores_data:
                    results["stores"] = stores_data

            if data_type in ["events", "all"]:
                events_data = self._search_events(query)
                if events_data:
                    results["events"] = events_data

            if data_type in ["narrative", "all"]:
                narrative_data = self._get_narrative_data()
                if narrative_data:
                    results["narrative"] = narrative_data

            return results

        except Exception as e:
            logger.error(f"Error searching data: {e}")
            return {"error": f"データ検索中にエラーが発生しました: {str(e)}"}

    def _search_stores(self, query: str, category: str = "") -> List[Dict[str, Any]]:
        """店舗データを検索する。"""
        if not self.stores_file.exists():
            return []

        try:
            results = []
            with open(self.stores_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # カテゴリフィルター
                    if category and row.get('category', '').lower() != category.lower():
                        continue

                    # クエリ検索（店舗名、説明、住所で検索）
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

    def _search_events(self, query: str) -> List[Dict[str, Any]]:
        """イベントデータを検索する。"""
        if not self.events_file.exists():
            return []

        try:
            results = []
            with open(self.events_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # クエリ検索（イベント名、説明、場所で検索）
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


class StoreInfoTool(BaseTool):
    """特定の店舗の詳細情報を取得するツール。"""

    def __init__(self) -> None:
        """店舗情報ツールを初期化する。"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.input_dir = self.project_root / "input"
        self.stores_file = self.input_dir / "filtered_store_data_20250926_052949.csv"

    @property
    def name(self) -> str:
        return "get_store_info"

    @property
    def description(self) -> str:
        return "店舗名を指定して、その店舗の詳細情報（営業時間、連絡先、住所など）を取得する。"

    def execute(self, **kwargs: Any) -> Any:
        """店舗の詳細情報を取得する。

        Args:
            store_name (str): 店舗名

        Returns:
            店舗の詳細情報
        """
        store_name = kwargs.get("store_name", "")

        if not store_name:
            return {"error": "店舗名を指定してください"}

        try:
            if not self.stores_file.exists():
                return {"error": "店舗データファイルが見つかりません"}

            with open(self.stores_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if store_name.lower() in row.get('store_name', '').lower():
                        return row

            return {"error": f"店舗「{store_name}」が見つかりませんでした"}

        except Exception as e:
            logger.error(f"Error getting store info: {e}")
            return {"error": f"店舗情報取得中にエラーが発生しました: {str(e)}"}


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
