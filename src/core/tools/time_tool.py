"""時刻関連ツール。"""

from datetime import datetime
from typing import Any

import pytz

from src.core.tools.base import BaseTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GetCurrentTimeTool(BaseTool):
    """指定されたタイムゾーンの現在時刻を取得するツール。"""

    @property
    def name(self) -> str:
        """ツール名。"""
        return "get_current_time"

    @property
    def description(self) -> str:
        """ツールの説明。"""
        return (
            "指定されたタイムゾーンの現在時刻を返します。"
            "timezone: タイムゾーン名"
            "（例: 'Asia/Tokyo', 'America/New_York'）"
        )

    def execute(self, timezone: str) -> str:  # type: ignore[override]
        """指定されたタイムゾーンの現在時刻を取得する。

        Args:
            timezone: タイムゾーン名（例: 'Asia/Tokyo', 'America/New_York'）

        Returns:
            現在時刻の文字列（曜日情報を含む）
        """
        try:
            tz = pytz.timezone(timezone)
            current_datetime = datetime.now(tz)
            current_time = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

            # 曜日情報を追加
            weekdays = {
                0: "月曜日",
                1: "火曜日",
                2: "水曜日",
                3: "木曜日",
                4: "金曜日",
                5: "土曜日",
                6: "日曜日"
            }
            weekday_name = weekdays[current_datetime.weekday()]
            result = f"{current_time} ({weekday_name})"

            logger.debug(f"Current time for {timezone}: {result}")
            return result
        except Exception as e:
            error_msg = f"タイムゾーンの取得に失敗しました: {e}"
            logger.error(error_msg)
            return error_msg

    def format_input(self, **kwargs: Any) -> str:
        """ツールの入力をフォーマットする（カスタム実装）。"""
        timezone = kwargs.get("timezone", "不明")
        return f"タイムゾーン: {timezone}"

    def format_output(self, output: Any) -> str:
        """ツールの出力をフォーマットする（カスタム実装）。"""
        return f"現在時刻: {output}"
