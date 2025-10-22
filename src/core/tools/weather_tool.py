"""天気情報取得ツール。"""

from typing import Any

import requests  # type: ignore

from src.core.tools.base import BaseTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class WeatherTool(BaseTool):
    """気象庁APIから天気予報を取得するツール。"""

    # 対応地域と地域コードのマッピング
    AREA_CODES = {
        "東京": "130000",
    }

    API_BASE_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast"
    TIMEOUT = 10  # APIリクエストのタイムアウト（秒）

    @property
    def name(self) -> str:
        """ツール名。"""
        return "get_weather"

    @property
    def description(self) -> str:
        """ツールの説明。"""
        return """指定された地域の1週間分の天気予報を取得します。

【対応地域】
- 東京

【取得できる情報】
- 今日から7日後までの天気予報（最大7日分）
- 各日の天気状態（晴れ、曇り、雨など）
- 各日の最低気温・最高気温

【使用例】
- location="東京" で東京の1週間分の天気予報を取得

【返り値】
- forecast配列に日ごとの天気情報が含まれます
- エージェントは返却されたデータから「明日」「明後日」「週末」などを判定して回答してください
"""

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """天気予報を取得する。

        Args:
            location: 都市名（例: "東京"）

        Returns:
            天気情報の辞書、エラー時は {"error": "エラーメッセージ"}
        """
        location = kwargs.get("location", "")

        if not location:
            return {"error": "都市名を指定してください"}

        try:
            # 地域コードを取得
            area_code = self._get_area_code(location)

            # 気象庁APIからデータを取得
            data = self._fetch_weather_data(area_code)

            # データを解析・整形
            result = self._parse_weather_info(data, location, area_code)

            logger.info(f"Successfully fetched weather data for {location}")
            return result

        except ValueError as e:
            error_msg = str(e)
            logger.warning(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"天気情報の取得に失敗しました: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}

    def _get_area_code(self, location: str) -> str:
        """都市名から地域コードを取得する。

        Args:
            location: 都市名

        Returns:
            地域コード

        Raises:
            ValueError: 未対応の都市の場合
        """
        area_code = self.AREA_CODES.get(location)
        if not area_code:
            raise ValueError(f"指定された地域はサポートされていません: {location}")
        return area_code

    def _fetch_weather_data(self, area_code: str) -> Any:
        """気象庁APIから天気データを取得する。

        Args:
            area_code: 地域コード

        Returns:
            APIレスポンスのJSON（辞書またはリスト）

        Raises:
            Exception: API呼び出しに失敗した場合
        """
        url = f"{self.API_BASE_URL}/{area_code}.json"
        logger.info(f"Fetching weather data from: {url}")

        try:
            response = requests.get(url, timeout=self.TIMEOUT)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout as e:
            raise Exception("気象庁APIへの接続がタイムアウトしました") from e
        except requests.exceptions.RequestException as e:
            raise Exception(f"気象庁APIへの接続に失敗しました: {str(e)}") from e

    def _parse_weather_info(self, data: Any, location: str, area_code: str) -> dict[str, Any]:
        """APIレスポンスから天気情報を抽出・整形する。

        Args:
            data: APIレスポンス（JSON配列）
            location: 都市名
            area_code: 地域コード

        Returns:
            整形された天気情報の辞書
        """
        try:
            # data[0]: 3日分の詳細予報（天気テキスト含む）
            # data[1]: 7日分の週間予報（気温含む）
            detail_data = data[0]
            weekly_data = data[1]

            # 発表元と発表日時を取得
            publishing_office = weekly_data.get("publishingOffice", "")
            report_datetime = weekly_data.get("reportDatetime", "")

            # data[0]から天気テキストを取得（3日分）
            detail_time_series = detail_data.get("timeSeries", [])
            if len(detail_time_series) < 1:
                raise ValueError("詳細天気データの形式が不正です")

            detail_weather_series = detail_time_series[0]
            detail_weather_areas = detail_weather_series.get("areas", [])

            # 東京地方の天気を取得
            tokyo_detail_area = None
            for area in detail_weather_areas:
                if area.get("area", {}).get("name") == "東京地方":
                    tokyo_detail_area = area
                    break

            detail_weathers = tokyo_detail_area.get("weathers", []) if tokyo_detail_area else []

            # data[1]から7日分の日付と気温を取得
            weekly_time_series = weekly_data.get("timeSeries", [])
            if len(weekly_time_series) < 2:
                raise ValueError("週間天気データの形式が不正です")

            # timeSeries[0]: 日付情報（weatherCodesもあるが使わない）
            # timeSeries[1]: 気温情報
            weather_series = weekly_time_series[0]
            weather_time_defines = weather_series.get("timeDefines", [])

            temp_series = weekly_time_series[1]
            temp_areas = temp_series.get("areas", [])

            # 東京の気温を取得
            tokyo_temp_area = None
            for area in temp_areas:
                if area.get("area", {}).get("name") == "東京":
                    tokyo_temp_area = area
                    break

            if not tokyo_temp_area:
                raise ValueError("東京の気温情報が見つかりません")

            temps_min = tokyo_temp_area.get("tempsMin", [])
            temps_max = tokyo_temp_area.get("tempsMax", [])

            # 予報データを組み立て（7日分）
            forecast = []
            for i in range(len(weather_time_defines)):
                date_str = weather_time_defines[i]
                # 日付部分のみを抽出（YYYY-MM-DD形式）
                date_only = date_str.split("T")[0] if "T" in date_str else date_str

                # 天気テキスト（3日分のみ利用可能）
                weather = ""
                if i < len(detail_weathers):
                    weather = detail_weathers[i]
                    weather = self._simplify_weather_text(weather)

                # 気温データを取得
                temp_min = temps_min[i] if i < len(temps_min) else ""
                temp_max = temps_max[i] if i < len(temps_max) else ""

                # 気温が空文字列でない場合のみ追加
                temp_data: dict[str, str] = {}
                if temp_min and temp_min != "":
                    temp_data["min"] = temp_min
                if temp_max and temp_max != "":
                    temp_data["max"] = temp_max

                forecast_item: dict[str, Any] = {
                    "date": date_only,
                    "weather": weather,
                }

                # 気温データがある場合のみ追加
                if temp_data:
                    forecast_item["temperature"] = temp_data

                forecast.append(forecast_item)

            logger.debug(f"Parsing weather data for {len(forecast)} days")

            return {
                "location": location,
                "area_code": area_code,
                "forecast": forecast,
                "publishing_office": publishing_office,
                "report_datetime": report_datetime,
            }

        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Failed to parse weather data: {str(e)}")
            raise ValueError("天気データの解析に失敗しました") from e

    def _simplify_weather_text(self, weather: str) -> str:
        """気象庁の詳細な天気文字列を簡潔に整形する。

        Args:
            weather: 元の天気文字列（例: "くもり　夜　雨"）

        Returns:
            簡潔に整形された天気文字列（例: "曇り時々雨"）
        """
        if not weather:
            return ""

        import re

        # 基本的な置換ルール
        weather = weather.replace("くもり", "曇り")
        weather = weather.replace("はれ", "晴れ")

        # 複数の空白・全角スペースを1つの空白に
        weather = re.sub(r"[\s\u3000]+", " ", weather)

        # 時間帯キーワード
        time_keywords = ["朝", "昼", "夕方", "夜", "昼前", "昼過ぎ", "明け方", "所により", "ところにより"]

        # 「から」「後」を「のち」に置換
        weather = weather.replace("から", "のち")
        weather = weather.replace("後", "のち")

        # スペースで分割
        parts = weather.split()

        # 時間帯キーワードを削除
        filtered_parts = [p for p in parts if p not in time_keywords]

        # 天気の主要部分を抽出
        if len(filtered_parts) == 0:
            return weather.strip()
        elif len(filtered_parts) == 1:
            return filtered_parts[0]
        else:
            # 複数の天気がある場合
            # 「のち」「時々」などの接続詞を探す
            if "のち" in filtered_parts:
                # 「のち」の前後を取得
                nochi_idx = filtered_parts.index("のち")
                before = filtered_parts[nochi_idx - 1] if nochi_idx > 0 else ""
                after = filtered_parts[nochi_idx + 1] if nochi_idx + 1 < len(filtered_parts) else ""
                if before and after:
                    return f"{before}のち{after}"
            elif "時々" in filtered_parts:
                # 「時々」の前後を取得
                tokidoki_idx = filtered_parts.index("時々")
                before = filtered_parts[tokidoki_idx - 1] if tokidoki_idx > 0 else ""
                after = filtered_parts[tokidoki_idx + 1] if tokidoki_idx + 1 < len(filtered_parts) else ""
                if before and after:
                    return f"{before}時々{after}"

            # 接続詞がない場合、最初と2番目の天気を「時々」で接続
            return f"{filtered_parts[0]}時々{filtered_parts[1]}"
