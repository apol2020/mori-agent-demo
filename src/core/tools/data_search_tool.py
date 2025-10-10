"""店舗・イベント・ナラティブデータを検索するツール。"""

import csv
from pathlib import Path
from typing import Any

from src.core.tools.base import BaseTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


def find_data_file(input_dir: Path, patterns: list[str], default_name: str) -> Path:
    """指定されたパターンでデータファイルを検索する。

    Args:
        input_dir: 検索対象ディレクトリ
        patterns: 検索パターンのリスト（優先順位順）
        default_name: 見つからない場合のデフォルトファイル名

    Returns:
        見つかったファイルのPath、見つからない場合はデフォルトPath
    """
    try:
        for pattern in patterns:
            matching_files = list(input_dir.glob(pattern))
            if matching_files:
                # 最新のファイルを選択（作成日時順）
                return max(matching_files, key=lambda p: p.stat().st_mtime)

        # 見つからない場合はデフォルトパスを返す
        return input_dir / default_name
    except Exception as e:
        logger.warning(f"Error finding file with patterns {patterns}: {e}")
        return input_dir / default_name


class StoreInfoTool(BaseTool):
    """特定の店舗の詳細情報を取得するツール。"""

    def __init__(self) -> None:
        """店舗情報ツールを初期化する。"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.input_dir = self.project_root / "input"
        # 店舗データファイルを動的に検索
        self.stores_file = find_data_file(
            self.input_dir, ["*store*.csv", "filtered_*.csv", "*店舗*.csv"], "filtered_store_data.csv"
        )

    @property
    def name(self) -> str:
        return "get_store_info"

    @property
    def description(self) -> str:
        return (
            "get_store_info: 店舗名を指定して、その店舗の詳細情報を取得する。"
            "使用データ: store_name, description, category, opening_hours, irregular_closures, phone, email, address。"
            "営業情報や連絡先の確認に使用。店舗IDは内部処理専用で、ユーザーには表示しない。"
        )

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

            with open(self.stores_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 店舗IDでの完全一致検索（優先）
                    if store_id and row.get("store_id", "").upper() == store_id.upper():
                        return row
                    # 店舗名での部分一致検索
                    if store_name and store_name.lower() in row.get("store_name", "").lower():
                        return row

            search_term = store_id if store_id else store_name
            return {"error": f"店舗「{search_term}」が見つかりませんでした"}

        except Exception as e:
            logger.error(f"Error getting store info: {e}")
            return {"error": f"店舗情報取得中にエラーが発生しました: {str(e)}"}


class EventInfoTool(BaseTool):
    """特定のイベントの詳細情報を取得するツール。"""

    def __init__(self) -> None:
        """イベント情報ツールを初期化する。"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.input_dir = self.project_root / "input"
        # イベントデータファイルを動的に検索
        self.events_file = find_data_file(
            self.input_dir, ["events*.csv", "*event*.csv", "*イベント*.csv"], "events.csv"
        )

    @property
    def name(self) -> str:
        return "get_event_info"

    @property
    def description(self) -> str:
        return (
            "get_event_info: イベント名を指定して、そのイベントの詳細情報を取得する。"
            "使用データ: event_name, description, date_time, location, capacity, contact_info, cost, "
            "registration_required, target_audience。イベント参加の検討に必要な情報を提供。"
        )

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

            with open(self.events_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if event_name.lower() in row.get("event_name", "").lower():
                        return row

            return {"error": f"イベント「{event_name}」が見つかりませんでした"}

        except Exception as e:
            logger.error(f"Error getting event info: {e}")
            return {"error": f"イベント情報取得中にエラーが発生しました: {str(e)}"}


class StoreHoursCheckTool(BaseTool):
    """店舗の営業時間をチェックし、現在営業中かどうかを判定するツール。"""

    def __init__(self) -> None:
        """営業時間チェックツールを初期化する。"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.input_dir = self.project_root / "input"
        # 店舗データファイルを動的に検索
        self.stores_file = find_data_file(
            self.input_dir, ["*store*.csv", "filtered_*.csv", "*店舗*.csv"], "filtered_store_data.csv"
        )

    @property
    def name(self) -> str:
        return "check_store_hours"

    @property
    def description(self) -> str:
        return (
            "check_store_hours: 店舗名を指定して、現在その店舗が営業中かどうかを確認する。"
            "使用データ: store_name, opening_hours, irregular_closures。"
            "営業時間と現在時刻を比較して判定し、営業状況、営業時間、臨時休業情報を提供する。"
            "店舗IDは内部処理専用で、ユーザーには表示しない。"
        )

    def execute(self, **kwargs: Any) -> Any:
        """店舗の営業状況を確認する。

        Args:
            store_name (str): 店舗名
            store_id (str, optional): [内部処理専用] 店舗ID（STR-0001形式） - ユーザーには非表示

        Returns:
            営業状況の詳細情報（店舗IDは含まれますが、ユーザーには表示しません）
        """
        store_name = kwargs.get("store_name", "")
        store_id = kwargs.get("store_id", "")

        if not store_name and not store_id:
            return {"error": "店舗名または店舗IDを指定してください"}

        try:
            if not self.stores_file.exists():
                return {"error": "店舗データファイルが見つかりません"}

            # 店舗情報を取得
            store_info = None
            with open(self.stores_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 店舗IDでの完全一致検索（優先）
                    if store_id and row.get("store_id", "").upper() == store_id.upper():
                        store_info = row
                        break
                    # 店舗名での部分一致検索
                    if store_name and store_name.lower() in row.get("store_name", "").lower():
                        store_info = row
                        break

            if not store_info:
                search_term = store_id if store_id else store_name
                return {"error": f"店舗「{search_term}」が見つかりませんでした"}

            # 営業時間情報を解析
            opening_hours = store_info.get("opening_hours", "").strip()
            irregular_closures = store_info.get("irregular_closures", "").strip()

            # 現在時刻を取得（日本時間）
            from datetime import datetime, timedelta, timezone

            jst = timezone(timedelta(hours=9))
            current_time = datetime.now(jst)
            current_hour = current_time.hour
            current_minute = current_time.minute
            current_weekday = current_time.weekday()  # 0=月曜日, 6=日曜日

            # 営業状況を判定
            is_open, status_message = self._check_business_status(
                opening_hours, current_hour, current_minute, current_weekday
            )

            return {
                "store_name": store_info.get("store_name", ""),
                "store_id": store_info.get("store_id", ""),
                "is_open": is_open,
                "status": status_message,
                "opening_hours": opening_hours,
                "irregular_closures": irregular_closures,
                "current_time": current_time.strftime("%Y年%m月%d日 %H:%M"),
                "check_time": current_time.isoformat(),
            }

        except Exception as e:
            logger.error(f"Error checking store hours: {e}")
            return {"error": f"営業時間確認中にエラーが発生しました: {str(e)}"}

    def _check_business_status(
        self, opening_hours: str, current_hour: int, current_minute: int, current_weekday: int
    ) -> tuple[bool, str]:
        """営業時間文字列を解析して現在の営業状況を判定する。

        Args:
            opening_hours: 営業時間の文字列
            current_hour: 現在の時（24時間制）
            current_minute: 現在の分
            current_weekday: 現在の曜日（0=月曜日, 6=日曜日）

        Returns:
            (is_open, status_message) のタプル
        """
        if not opening_hours or opening_hours == "情報なし":
            return False, "営業時間情報が利用できません"

        try:
            # 現在時刻を分単位に変換
            current_minutes = current_hour * 60 + current_minute

            # 簡易的な営業時間パース（例: "10:00-22:00"）
            import re

            # 24時間営業の場合
            if "24時間" in opening_hours or "24hour" in opening_hours.lower():
                return True, "24時間営業中"

            # 定休日の確認
            weekday_names = ["月", "火", "水", "木", "金", "土", "日"]
            current_day_name = weekday_names[current_weekday]

            if f"{current_day_name}曜" in opening_hours and "休" in opening_hours:
                return False, f"{current_day_name}曜日は定休日"

            # 時間形式のパース（HH:MM-HH:MM）
            time_pattern = r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})"
            matches = re.findall(time_pattern, opening_hours)

            if matches:
                # 最初にマッチした営業時間を使用
                start_h, start_m, end_h, end_m = map(int, matches[0])
                start_minutes = start_h * 60 + start_m
                end_minutes = end_h * 60 + end_m

                # 深夜営業の場合（翌日まで）
                if end_minutes <= start_minutes:
                    end_minutes += 24 * 60
                    if current_minutes < start_minutes:
                        current_minutes += 24 * 60

                if start_minutes <= current_minutes <= end_minutes:
                    return True, f"営業中（{start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}）"
                else:
                    return False, f"営業時間外（営業時間: {start_h:02d}:{start_m:02d}-{end_h:02d}:{end_m:02d}）"

            # パースできない場合
            return False, f"営業時間: {opening_hours} (判定不可)"

        except Exception as e:
            logger.warning(f"Error parsing opening hours: {e}")
            return False, f"営業時間: {opening_hours} (解析エラー)"
