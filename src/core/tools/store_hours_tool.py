"""店舗営業時間チェックツール。"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pytz

from src.core.tools.base import BaseTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class StoreHoursCheckTool(BaseTool):
    """店舗の営業時間をチェックして、現在営業中かどうかを判定するツール。"""

    def __init__(self) -> None:
        """店舗営業時間チェックツールを初期化する。"""
        self.project_root = Path(__file__).parent.parent.parent.parent
        self.input_dir = self.project_root / "input"
        self.stores_file = self.input_dir / "filtered_store_data_20250926_052949.csv"

    @property
    def name(self) -> str:
        return "check_store_hours"

    @property
    def description(self) -> str:
        return "店舗名を指定して、現在その店舗が営業中かどうかを確認する。営業時間と現在時刻を比較して判定する。"

    def execute(self, **kwargs: Any) -> Any:
        """店舗が現在営業中かどうかをチェックする。

        Args:
            store_name (str): 店舗名
            timezone (str, optional): タイムゾーン（デフォルト: 'Asia/Tokyo'）

        Returns:
            営業状況の判定結果
        """
        store_name = kwargs.get("store_name", "")
        timezone = kwargs.get("timezone", "Asia/Tokyo")

        if not store_name:
            return {"error": "店舗名を指定してください"}

        try:
            # 現在の日時を取得
            tz = pytz.timezone(timezone)
            current_datetime = datetime.now(tz)
            current_weekday = current_datetime.weekday()  # 0=月曜日, 6=日曜日
            current_time = current_datetime.time()

            # 曜日名のマッピング
            weekday_names = {
                0: "monday",
                1: "tuesday",
                2: "wednesday",
                3: "thursday",
                4: "friday",
                5: "saturday",
                6: "sunday"
            }
            current_day_name = weekday_names[current_weekday]

            # 店舗情報を取得
            store_info = self._get_store_info(store_name)
            if "error" in store_info:
                return store_info

            # 営業時間データを解析
            opening_hours = store_info.get("opening_hours", "")
            if not opening_hours:
                return {
                    "store_name": store_name,
                    "current_time": current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    "is_open": None,
                    "message": "営業時間の情報がありません"
                }

            # JSONデータをパース
            try:
                hours_data = json.loads(opening_hours)
            except json.JSONDecodeError:
                return {
                    "store_name": store_name,
                    "current_time": current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    "is_open": None,
                    "message": "営業時間のデータ形式が不正です"
                }

            # 今日の営業時間を確認
            today_hours = hours_data.get(current_day_name)

            if today_hours is None:
                return {
                    "store_name": store_name,
                    "current_time": current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    "is_open": False,
                    "message": f"本日（{self._get_weekday_japanese(current_weekday)}）は定休日です"
                }

            # 営業時間をチェック
            is_open = False
            open_periods = []

            if isinstance(today_hours, list):
                for period in today_hours:
                    if isinstance(period, dict) and "open" in period and "close" in period:
                        open_time = datetime.strptime(period["open"], "%H:%M").time()
                        close_time = datetime.strptime(period["close"], "%H:%M").time()

                        open_periods.append(f"{period['open']}-{period['close']}")

                        if open_time <= current_time <= close_time:
                            is_open = True

            # 臨時休業をチェック
            irregular_closures = store_info.get("irregular_closures", "")
            closure_message = ""
            if irregular_closures:
                try:
                    closures_data = json.loads(irregular_closures)
                    if isinstance(closures_data, list):
                        current_date_str = current_datetime.strftime("%Y-%m-%d")
                        for closure in closures_data:
                            if isinstance(closure, dict):
                                closure_date = closure.get("date")
                                if closure_date == current_date_str:
                                    is_open = False
                                    closure_message = f"本日は臨時休業です（理由: {closure.get('reason', '不明')}）"
                                    break
                except (json.JSONDecodeError, TypeError):
                    pass

            # 結果をまとめる
            result = {
                "store_name": store_name,
                "current_time": current_datetime.strftime("%Y-%m-%d %H:%M:%S"),
                "current_day": self._get_weekday_japanese(current_weekday),
                "is_open": is_open,
                "opening_hours_today": open_periods if open_periods else ["定休日"]
            }

            if closure_message:
                result["message"] = closure_message
            elif is_open:
                result["message"] = "現在営業中です"
            elif not open_periods:
                result["message"] = "本日は定休日です"
            else:
                result["message"] = "現在営業時間外です"

            return result

        except Exception as e:
            logger.error(f"Error checking store hours: {e}")
            return {"error": f"営業時間チェック中にエラーが発生しました: {str(e)}"}

    def _get_store_info(self, store_name: str) -> Dict[str, Any]:
        """店舗情報を取得する。"""
        if not self.stores_file.exists():
            return {"error": "店舗データファイルが見つかりません"}

        try:
            with open(self.stores_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if store_name.lower() in row.get('store_name', '').lower():
                        return row

            return {"error": f"店舗「{store_name}」が見つかりませんでした"}

        except Exception as e:
            logger.error(f"Error getting store info: {e}")
            return {"error": f"店舗情報取得中にエラーが発生しました: {str(e)}"}

    def _get_weekday_japanese(self, weekday: int) -> str:
        """曜日番号を日本語に変換する。"""
        weekdays = {
            0: "月曜日",
            1: "火曜日",
            2: "水曜日",
            3: "木曜日",
            4: "金曜日",
            5: "土曜日",
            6: "日曜日"
        }
        return weekdays.get(weekday, "不明")
