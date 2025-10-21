"""WeatherToolのユニットテスト。"""

from unittest.mock import Mock, patch

import pytest

from src.core.tools.weather_tool import WeatherTool


class TestWeatherTool:
    """WeatherToolのテスト。"""

    def test_tool_name(self) -> None:
        """ツール名が正しいことを確認。"""
        tool = WeatherTool()
        assert tool.name == "get_weather"

    def test_tool_description(self) -> None:
        """ツールの説明が正しいことを確認。"""
        tool = WeatherTool()
        assert "天気予報" in tool.description
        assert "東京" in tool.description
        assert "1週間" in tool.description or "7日" in tool.description
        assert tool.description != ""

    def test_get_area_code_tokyo(self) -> None:
        """東京の地域コードが正しく取得できることを確認。"""
        tool = WeatherTool()
        area_code = tool._get_area_code("東京")
        assert area_code == "130000"

    def test_get_area_code_unsupported_city(self) -> None:
        """未対応の都市でValueErrorが発生することを確認。"""
        tool = WeatherTool()
        with pytest.raises(ValueError) as exc_info:
            tool._get_area_code("大阪")
        assert "サポートされていません" in str(exc_info.value)

    def test_execute_without_location(self) -> None:
        """都市名なしでエラーが返されることを確認。"""
        tool = WeatherTool()
        result = tool.execute()
        assert "error" in result
        assert "都市名" in result["error"]

    @patch("requests.get")
    def test_fetch_weather_data_success(self, mock_get: Mock) -> None:
        """気象庁APIからデータを正常に取得できることを確認。"""
        # モックレスポンスを設定
        mock_response = Mock()
        mock_response.json.return_value = [
            {"publishingOffice": "気象庁", "timeSeries": []},
            {"publishingOffice": "気象庁", "timeSeries": []},
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        tool = WeatherTool()
        data = tool._fetch_weather_data("130000")

        # APIが呼ばれたことを確認
        mock_get.assert_called_once()
        assert "https://www.jma.go.jp/bosai/forecast/data/forecast/130000.json" in mock_get.call_args[0][0]
        assert isinstance(data, list)

    @patch("requests.get")
    def test_fetch_weather_data_timeout(self, mock_get: Mock) -> None:
        """API接続がタイムアウトした場合にExceptionが発生することを確認。"""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout()

        tool = WeatherTool()
        with pytest.raises(Exception) as exc_info:
            tool._fetch_weather_data("130000")
        assert "タイムアウト" in str(exc_info.value)

    def test_parse_weather_info(self) -> None:
        """天気データの解析が正しく行われることを確認。"""
        # 実際のAPIレスポンスに近いモックデータ
        mock_data = [
            # data[0]: 詳細予報（3日分）
            {
                "publishingOffice": "気象庁",
                "reportDatetime": "2025-10-21T11:00:00+09:00",
                "timeSeries": [
                    {
                        "timeDefines": [
                            "2025-10-22T00:00:00+09:00",
                            "2025-10-23T00:00:00+09:00",
                            "2025-10-24T00:00:00+09:00",
                        ],
                        "areas": [
                            {
                                "area": {"name": "東京地方", "code": "130010"},
                                "weathers": ["くもり　夜　雨", "雨　昼前　から　くもり", "くもり　時々　晴れ"],
                            }
                        ],
                    }
                ],
            },
            # data[1]: 週間予報（7日分）
            {
                "publishingOffice": "気象庁",
                "reportDatetime": "2025-10-21T11:00:00+09:00",
                "timeSeries": [
                    {
                        "timeDefines": [
                            "2025-10-22T00:00:00+09:00",
                            "2025-10-23T00:00:00+09:00",
                            "2025-10-24T00:00:00+09:00",
                            "2025-10-25T00:00:00+09:00",
                            "2025-10-26T00:00:00+09:00",
                            "2025-10-27T00:00:00+09:00",
                            "2025-10-28T00:00:00+09:00",
                        ],
                        "areas": [{"area": {"name": "東京地方", "code": "130010"}}],
                    },
                    {
                        "timeDefines": [
                            "2025-10-22T00:00:00+09:00",
                            "2025-10-23T00:00:00+09:00",
                            "2025-10-24T00:00:00+09:00",
                            "2025-10-25T00:00:00+09:00",
                            "2025-10-26T00:00:00+09:00",
                            "2025-10-27T00:00:00+09:00",
                            "2025-10-28T00:00:00+09:00",
                        ],
                        "areas": [
                            {
                                "area": {"name": "東京", "code": "44132"},
                                "tempsMin": ["", "12", "12", "12", "14", "16", "14"],
                                "tempsMax": ["", "19", "20", "20", "19", "22", "20"],
                            }
                        ],
                    },
                ],
            },
        ]

        tool = WeatherTool()
        result = tool._parse_weather_info(mock_data, "東京", "130000")

        # 基本情報の確認
        assert result["location"] == "東京"
        assert result["area_code"] == "130000"
        assert result["publishing_office"] == "気象庁"
        assert result["report_datetime"] == "2025-10-21T11:00:00+09:00"

        # 予報データの確認
        assert "forecast" in result
        forecast = result["forecast"]
        assert len(forecast) == 7  # 7日分

        # 1日目のデータ確認
        assert forecast[0]["date"] == "2025-10-22"
        assert forecast[0]["weather"] != ""  # 天気情報があること

        # 2日目以降の気温データ確認
        assert "temperature" in forecast[1]
        assert forecast[1]["temperature"]["min"] == "12"
        assert forecast[1]["temperature"]["max"] == "19"

    def test_simplify_weather_text_basic(self) -> None:
        """天気テキストの簡潔化が正しく行われることを確認。"""
        tool = WeatherTool()

        # 基本的な置換
        assert "曇り" in tool._simplify_weather_text("くもり")
        assert "晴れ" in tool._simplify_weather_text("はれ")

        # 時間帯情報の削除
        result = tool._simplify_weather_text("くもり　夜　雨")
        assert "曇り" in result
        assert "雨" in result

        # 「から」→「のち」
        result = tool._simplify_weather_text("雨　昼前　から　くもり")
        assert "のち" in result or ("雨" in result and "曇り" in result)

    def test_simplify_weather_text_empty(self) -> None:
        """空の天気テキストが正しく処理されることを確認。"""
        tool = WeatherTool()
        assert tool._simplify_weather_text("") == ""

    @patch("requests.get")
    def test_execute_success(self, mock_get: Mock) -> None:
        """execute()が正常に動作することを確認。"""
        # モックレスポンスを設定
        mock_response = Mock()
        mock_response.json.return_value = [
            {
                "publishingOffice": "気象庁",
                "reportDatetime": "2025-10-21T11:00:00+09:00",
                "timeSeries": [
                    {
                        "timeDefines": ["2025-10-22T00:00:00+09:00"],
                        "areas": [{"area": {"name": "東京地方", "code": "130010"}, "weathers": ["晴れ"]}],
                    }
                ],
            },
            {
                "publishingOffice": "気象庁",
                "reportDatetime": "2025-10-21T11:00:00+09:00",
                "timeSeries": [
                    {"timeDefines": ["2025-10-22T00:00:00+09:00"], "areas": []},
                    {
                        "timeDefines": ["2025-10-22T00:00:00+09:00"],
                        "areas": [
                            {
                                "area": {"name": "東京", "code": "44132"},
                                "tempsMin": ["12"],
                                "tempsMax": ["20"],
                            }
                        ],
                    },
                ],
            },
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        tool = WeatherTool()
        result = tool.execute(location="東京")

        # エラーがないことを確認
        assert "error" not in result
        assert result["location"] == "東京"
        assert "forecast" in result
        assert len(result["forecast"]) > 0

    @patch("requests.get")
    def test_execute_unsupported_city(self, mock_get: Mock) -> None:
        """未対応の都市でエラーが返されることを確認。"""
        tool = WeatherTool()
        result = tool.execute(location="大阪")

        # エラーが返されることを確認
        assert "error" in result
        assert "サポートされていません" in result["error"]

        # APIが呼ばれていないことを確認
        mock_get.assert_not_called()

    @patch("requests.get")
    def test_execute_api_error(self, mock_get: Mock) -> None:
        """API接続エラー時にエラーが返されることを確認。"""
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        tool = WeatherTool()
        result = tool.execute(location="東京")

        # エラーが返されることを確認
        assert "error" in result
        assert "取得に失敗" in result["error"]

    def test_tool_is_reusable(self) -> None:
        """同じツールインスタンスを複数回使用できることを確認。"""
        tool = WeatherTool()

        # 複数回呼び出し可能
        name1 = tool.name
        name2 = tool.name
        assert name1 == name2 == "get_weather"

        desc1 = tool.description
        desc2 = tool.description
        assert desc1 == desc2
