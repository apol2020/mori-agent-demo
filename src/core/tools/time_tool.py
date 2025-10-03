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
            現在時刻の文字列
        """
        try:
            tz = pytz.timezone(timezone)
            current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
            logger.debug(f"Current time for {timezone}: {current_time}")
            return current_time
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
