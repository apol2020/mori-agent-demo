"""ツールレジストリ - ツールの明示的な登録と管理。"""

from typing import Any, Optional

from src.core.tools.base import BaseTool
from src.utils.logger import get_logger

try:
    from langchain_core.tools import tool
except ImportError as e:
    raise ImportError("langchain-core is required. Install it with: pip install langchain-core") from e

logger = get_logger(__name__)


class ToolRegistry:
    """ツールを明示的に登録・管理するレジストリクラス。"""

    def __init__(self) -> None:
        """ツールレジストリを初期化する。"""
        self._tools: dict[str, BaseTool] = {}
        self._langchain_tools: list[Any] = []

    def register_tool(self, tool_instance: BaseTool) -> None:
        """ツールを明示的に登録する。

        Args:
            tool_instance: 登録するツールのインスタンス

        Raises:
            ValueError: 同じ名前のツールが既に登録されている場合
        """
        tool_name = tool_instance.name
        if tool_name in self._tools:
            raise ValueError(f"Tool '{tool_name}' is already registered")

        # ツールインスタンスを保存
        self._tools[tool_name] = tool_instance
        logger.info(f"Registered tool: {tool_name}")

        # LangChain互換ツールを作成
        langchain_tool = self._create_langchain_tool(tool_instance)
        self._langchain_tools.append(langchain_tool)

    def _create_langchain_tool(self, tool_instance: BaseTool) -> Any:
        """BaseToolインスタンスからLangChain互換ツールを作成する。

        Args:
            tool_instance: ツールインスタンス

        Returns:
            LangChain互換ツール
        """
        tool_name = tool_instance.name
        tool_description = tool_instance.description

        # ツールインスタンスごとに適切な型注釈付き関数を作成
        if tool_name == "search_events":

            @tool
            def search_events(sql_query: str) -> dict:
                """イベントデータをSQLクエリで検索します。

                Args:
                    sql_query: 実行するSQLクエリ（SELECT文のみ）

                Returns:
                    検索結果の辞書（results: 結果リスト, count: 件数）
                """
                return tool_instance.execute(sql_query=sql_query)

            return search_events

        elif tool_name == "search_stores":

            @tool
            def search_stores(sql_query: str) -> dict:
                """店舗データをSQLクエリで検索します。

                Args:
                    sql_query: 実行するSQLクエリ（SELECT文のみ）

                Returns:
                    検索結果の辞書（results: 結果リスト, count: 件数）
                """
                return tool_instance.execute(sql_query=sql_query)

            return search_stores

        elif tool_name == "get_weather":

            @tool
            def get_weather(location: str) -> dict:
                """指定された地域の1週間分の天気予報を取得します。

                Args:
                    location: 都市名（例: 東京）

                Returns:
                    天気情報の辞書（最大7日分の天気、気温）
                """
                return tool_instance.execute(location=location)

            return get_weather

        elif tool_name == "search_products":

            @tool
            def search_products(sql_query: str) -> dict:
                """商品データをSQLクエリで検索します。

                Args:
                    sql_query: 実行するSQLクエリ（SELECT文のみ）

                Returns:
                    検索結果の辞書（results: 結果リスト, count: 件数）
                """
                return tool_instance.execute(sql_query=sql_query)

            return search_products

        elif tool_name == "get_user_profile":

            @tool
            def get_user_profile() -> dict:
                """対話中のユーザーのプロファイル情報を取得します。

                パラメータなしで呼び出すと、ログイン中のユーザーの嗜好情報を自動取得します。

                Returns:
                    ユーザー情報の辞書（username, profile_id, age, gender, preferences）
                """
                return tool_instance.execute()

            return get_user_profile

        else:
            # デフォルトの汎用ツール（型注釈なし）
            @tool
            def dynamic_tool(**kwargs: Any) -> Any:
                """動的に生成されたツール。"""
                return tool_instance.execute(**kwargs)

            dynamic_tool.name = tool_name
            dynamic_tool.description = tool_description
            return dynamic_tool

    def get_all_tools(self) -> list[Any]:
        """登録されているすべてのLangChain互換ツールを取得する。

        Returns:
            LangChain互換ツールのリスト
        """
        return self._langchain_tools.copy()

    def get_tool_instance(self, tool_name: str) -> Optional[BaseTool]:
        """ツール名からツールインスタンスを取得する。

        Args:
            tool_name: ツール名

        Returns:
            ツールインスタンス、見つからない場合はNone
        """
        return self._tools.get(tool_name)

    def get_all_tool_instances(self) -> dict[str, BaseTool]:
        """登録されているすべてのツールインスタンスを取得する。

        Returns:
            ツール名をキーとしたツールインスタンスの辞書
        """
        return self._tools.copy()

    def get_tool_descriptions(self) -> list[dict[str, str]]:
        """すべてのツールの名前と説明を取得する。

        Returns:
            ツールの名前と説明を含む辞書のリスト
        """
        return [{"name": tool.name, "description": tool.description} for tool in self._tools.values()]
