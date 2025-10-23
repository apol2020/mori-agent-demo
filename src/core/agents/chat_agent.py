"""ビジネスロジックを含むチャットエージェント実装。"""

import json
from collections.abc import AsyncIterator
from typing import Any, Optional

from src.config.prompts import get_agent_system_prompt
from src.core.agents.base_agent import BaseAgent
from src.core.common.output_normalizer import OutputNormalizer
from src.core.tools import tool_registry
from src.infrastructure.llm.anthropic_client import AnthropicClient
from src.infrastructure.llm.langchain_adapter import LangChainAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class ChatAgent(BaseAgent):
    """ビジネスロジックとツール管理を備えたチャットエージェント。

    このエージェント実装は、チャットインタラクション、ツールのセットアップ、
    会話管理のコアビジネスロジックを含む。フレームワーク固有の統合には
    LangChainAdapterを使用する。
    """

    def __init__(
        self,
        model_id: str = "claude-sonnet-4-20250514",
        anthropic_client: Optional[AnthropicClient] = None,
        username: Optional[str] = None,
    ) -> None:
        """チャットエージェントを初期化する。

        Args:
            model_id: 使用するモデルID
            anthropic_client: Anthropicクライアントインスタンス（後方互換性のため）
            username: ログイン中のユーザー名（ナラティブデータのフィルタリングに使用）
        """
        # ユーザー名が指定されている場合は専用のツールレジストリを作成
        if username:
            from src.core.tools import (
                EventSearchTool,
                ProductSearchTool,
                StoreSearchTool,
                ToolRegistry,
                UserProfileTool,
                WeatherTool,
            )

            user_tool_registry = ToolRegistry()
            user_tool_registry.register_tool(EventSearchTool())
            user_tool_registry.register_tool(StoreSearchTool())
            user_tool_registry.register_tool(ProductSearchTool())
            user_tool_registry.register_tool(WeatherTool())
            user_tool_registry.register_tool(UserProfileTool(username=username))
            self._tools = user_tool_registry.get_all_tools()
            self._tool_instances = user_tool_registry.get_all_tool_instances()
        else:
            # ユーザー名が指定されていない場合はグローバルレジストリを使用（後方互換性）
            self._tools = tool_registry.get_all_tools()
            self._tool_instances = tool_registry.get_all_tool_instances()

        self._prompt_template = get_agent_system_prompt()

        # LLMファクトリーを使用してLLMインスタンスを作成
        from src.infrastructure.llm.llm_factory import create_llm

        llm = create_llm(model_id, streaming=True)

        self._adapter = LangChainAdapter(
            llm=llm,
            tools=self._tools,
            prompt_template=self._prompt_template,
        )
        self._output_normalizer = OutputNormalizer()
        logger.info(f"ChatAgent initialized with model {model_id} and {len(self._tools)} tools")

    def _parse_tool_input(self, tool_input: Any) -> dict[str, Any]:
        """ツール入力を辞書形式にパースする。

        Args:
            tool_input: ツール入力（辞書、文字列、その他）

        Returns:
            パースされた辞書
        """
        if isinstance(tool_input, dict):
            return tool_input
        if isinstance(tool_input, str) and tool_input.strip():
            try:
                return json.loads(tool_input)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse tool input as JSON: {tool_input[:100]}")
        return {}

    def _format_tool_data(self, data: Any, is_dict: bool = True) -> str:
        """ツールデータをフォーマットする。

        Args:
            data: フォーマットするデータ
            is_dict: データが辞書かどうか

        Returns:
            フォーマットされた文字列
        """
        if is_dict and isinstance(data, dict):
            return json.dumps(data, ensure_ascii=False)
        return str(data)

    def _format_tool_execution(self, tool_info: dict[str, Any]) -> dict[str, str]:
        """ツール実行情報をフォーマットする。

        Args:
            tool_info: ツール実行情報（tool_name, tool_input, tool_output）

        Returns:
            フォーマットされたツール実行情報
        """
        tool_name = tool_info.get("tool_name", "unknown")
        tool_input = tool_info.get("tool_input", {})
        tool_output = tool_info.get("tool_output", "")

        # ツールインスタンスを取得してフォーマット
        tool_instance = self._tool_instances.get(tool_name)
        if tool_instance:
            try:
                input_dict = self._parse_tool_input(tool_input)
                formatted_input = tool_instance.format_input(**input_dict)
                formatted_output = tool_instance.format_output(tool_output)
            except Exception as e:
                logger.warning(f"Failed to format tool execution for {tool_name}: {e}")
                formatted_input = self._format_tool_data(tool_input, isinstance(tool_input, dict))
                formatted_output = str(tool_output)
        else:
            # ツールインスタンスがない場合はデフォルトフォーマット
            formatted_input = self._format_tool_data(tool_input, isinstance(tool_input, dict))
            formatted_output = str(tool_output)

        return {
            "tool_name": tool_name,
            "input_data": formatted_input,
            "output_data": formatted_output,
        }

    async def astream_response(
        self,
        user_input: str,
        session_id: str = "default",
    ) -> AsyncIterator[tuple[str, Optional[dict[str, str]]]]:
        """エージェント応答を非同期でストリーミングする。

        Args:
            user_input: ユーザーの入力メッセージ
            session_id: 会話コンテキストのセッションID

        Yields:
            (content, tool_execution)のタプル
            - content: AIからの応答チャンク
            - tool_execution: ツール実行情報（ツール実行時のみ）
              {"tool_name": str, "input_data": str, "output_data": str}
        """
        try:
            logger.info(f"Processing user input: {user_input[:100]}...")
            full_response = ""

            # アダプターからストリーミングしてメッセージを処理
            async for message_type, content, tool_info in self._adapter.astream(
                user_input=user_input,
                session_id=session_id,
            ):
                if message_type in ("ai", "AIMessageChunk") and content:
                    normalized_content = self._output_normalizer.normalize(content)
                    if normalized_content:
                        full_response += normalized_content
                        yield (normalized_content, None)
                elif message_type == "tool" and tool_info:
                    # ツール実行情報をフォーマット（店舗IDなどの内部情報を除去）
                    tool_execution = self._format_tool_execution(tool_info)
                    # ツール出力からも内部情報を除去
                    if tool_execution and "output_data" in tool_execution:
                        tool_execution["output_data"] = self._output_normalizer.normalize(tool_execution["output_data"])
                    yield ("", tool_execution)

            logger.info(f"Response generated successfully, length: {len(full_response)}")

        except Exception as e:
            error_msg = f"エラーが発生しました: {e}"
            logger.error(error_msg)
            yield (error_msg, None)

    async def ainvoke(
        self,
        user_input: str,
        session_id: str = "default",
    ) -> dict[str, Any]:
        """ストリーミングなしでエージェントを非同期で呼び出す。

        Args:
            user_input: ユーザーの入力メッセージ
            session_id: 会話コンテキストのセッションID

        Returns:
            出力とメッセージを含む辞書
        """
        try:
            logger.info(f"Invoking agent with input: {user_input[:100]}...")

            result = await self._adapter.ainvoke(
                user_input=user_input,
                session_id=session_id,
            )

            # 結果から出力を抽出
            output = ""
            if "messages" in result:
                for message in result["messages"]:
                    if hasattr(message, "type") and message.type == "ai":
                        if hasattr(message, "content"):
                            output = self._output_normalizer.normalize(message.content)

            logger.info("Agent invocation completed successfully")
            return {
                "output": output,
                "messages": result.get("messages", []),
            }

        except Exception as e:
            error_msg = f"エージェントの実行中にエラーが発生しました: {e}"
            logger.error(error_msg)
            return {
                "output": error_msg,
                "messages": [],
            }
