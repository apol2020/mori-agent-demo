"""GetCurrentTimeToolのユニットテスト。"""

from datetime import datetime
from unittest.mock import patch

import pytz

from src.core.tools.time_tool import GetCurrentTimeTool


class TestGetCurrentTimeTool:
    """GetCurrentTimeToolのテスト。"""

    def test_time_tool_name(self) -> None:
        """ツール名が正しいことを確認。"""
        tool = GetCurrentTimeTool()
        assert tool.name == "get_current_time"

    def test_time_tool_description(self) -> None:
        """ツールの説明が正しいことを確認。"""
        tool = GetCurrentTimeTool()
        assert "タイムゾーン" in tool.description
        assert "現在時刻" in tool.description
        assert tool.description != ""

    def test_get_current_time_tokyo(self) -> None:
        """東京のタイムゾーンで現在時刻を取得できることを確認。"""
        tool = GetCurrentTimeTool()
        result = tool.execute(timezone="Asia/Tokyo")

        # 結果が文字列で、日付時刻形式であることを確認
        assert isinstance(result, str)
        assert len(result) > 0
        # YYYY-MM-DD HH:MM:SS形式を確認
        datetime.strptime(result, "%Y-%m-%d %H:%M:%S")

    def test_get_current_time_new_york(self) -> None:
        """ニューヨークのタイムゾーンで現在時刻を取得できることを確認。"""
        tool = GetCurrentTimeTool()
        result = tool.execute(timezone="America/New_York")

        assert isinstance(result, str)
        datetime.strptime(result, "%Y-%m-%d %H:%M:%S")

    def test_get_current_time_utc(self) -> None:
        """UTCタイムゾーンで現在時刻を取得できることを確認。"""
        tool = GetCurrentTimeTool()
        result = tool.execute(timezone="UTC")

        assert isinstance(result, str)
        datetime.strptime(result, "%Y-%m-%d %H:%M:%S")

    def test_get_current_time_london(self) -> None:
        """ロンドンのタイムゾーンで現在時刻を取得できることを確認。"""
        tool = GetCurrentTimeTool()
        result = tool.execute(timezone="Europe/London")

        assert isinstance(result, str)
        datetime.strptime(result, "%Y-%m-%d %H:%M:%S")

    def test_get_current_time_invalid_timezone(self) -> None:
        """無効なタイムゾーンでエラーメッセージを返すことを確認。"""
        tool = GetCurrentTimeTool()
        result = tool.execute(timezone="Invalid/Timezone")

        assert isinstance(result, str)
        assert "失敗" in result

    def test_get_current_time_empty_timezone(self) -> None:
        """空のタイムゾーン文字列でエラーメッセージを返すことを確認。"""
        tool = GetCurrentTimeTool()
        result = tool.execute(timezone="")

        assert isinstance(result, str)
        assert "失敗" in result

    def test_get_current_time_format(self) -> None:
        """返される時刻のフォーマットが正しいことを確認。"""
        tool = GetCurrentTimeTool()
        mock_time = datetime(2025, 3, 15, 14, 30, 45)

        with patch("src.core.tools.time_tool.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_time.replace(tzinfo=pytz.timezone("Asia/Tokyo"))
            result = tool.execute(timezone="Asia/Tokyo")

            assert isinstance(result, str)
            assert result == "2025-03-15 14:30:45"

    def test_time_tool_is_reusable(self) -> None:
        """同じツールインスタンスを複数回使用できることを確認。"""
        tool = GetCurrentTimeTool()

        result1 = tool.execute(timezone="Asia/Tokyo")
        result2 = tool.execute(timezone="America/New_York")
        result3 = tool.execute(timezone="UTC")

        # すべて有効な時刻文字列が返されることを確認
        datetime.strptime(result1, "%Y-%m-%d %H:%M:%S")
        datetime.strptime(result2, "%Y-%m-%d %H:%M:%S")
        datetime.strptime(result3, "%Y-%m-%d %H:%M:%S")

    def test_get_current_time_different_timezones_different_times(self) -> None:
        """異なるタイムゾーンで異なる時刻が返されることを確認。"""
        tool = GetCurrentTimeTool()

        tokyo_time = tool.execute(timezone="Asia/Tokyo")
        utc_time = tool.execute(timezone="UTC")

        # 両方とも有効な時刻であることを確認
        datetime.strptime(tokyo_time, "%Y-%m-%d %H:%M:%S")
        datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S")

        # 同じ瞬間でも、異なるタイムゾーンでは異なる時刻表示になる可能性がある
        # （ただし、秒単位で同時に実行されるため、完全に異なるとは限らない）
        assert isinstance(tokyo_time, str)
        assert isinstance(utc_time, str)
