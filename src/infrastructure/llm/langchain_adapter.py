"""LLM統合用のLangChainフレームワークアダプター。"""

import json
from collections.abc import AsyncIterator
from typing import Any, Optional

from src.utils.logger import get_logger

try:
    from langchain_core.messages import SystemMessage
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.prebuilt import create_react_agent
except ImportError as e:
    raise ImportError("langgraph is required. Install it with: pip install langgraph") from e

logger = get_logger(__name__)


class LangChainAdapter:
    """LangChainフレームワーク統合用のアダプター。

    このクラスはLangChain/LangGraphの薄い抽象化レイヤーを提供し、
    フレームワーク固有の実装詳細のみを処理する。
    """

    def __init__(
        self,
        llm: Any,
        tools: list[Any],
        prompt_template: Optional[SystemMessage] = None,
    ) -> None:
        """LangChainアダプターを初期化する。

        Args:
            llm: LLMインスタンス（ChatAnthropic、ChatOpenAIなど）
            tools: LangChain互換ツールのリスト
            prompt_template: エージェントのシステムプロンプト (SystemMessage)
        """
        self._llm = llm
        self._tools = tools
        self._system_prompt = prompt_template
        self._memory: Any = MemorySaver()
        self._agent: Optional[Any] = None
        self._setup_agent()

    def _setup_agent(self) -> None:
        """LangGraph ReActエージェントをセットアップする。"""
        try:
            logger.info(f"Creating LangGraph ReAct agent with {len(self._tools)} tools")

            # システムプロンプトがある場合はpromptパラメータとして設定
            if self._system_prompt:
                self._agent = create_react_agent(
                    model=self._llm,
                    tools=self._tools,
                    checkpointer=self._memory,
                    prompt=self._system_prompt,
                )
                logger.info("LangGraph agent created with custom system prompt")
            else:
                self._agent = create_react_agent(
                    model=self._llm,
                    tools=self._tools,
                    checkpointer=self._memory,
                )
                logger.info("LangGraph agent created with default prompt")

        except Exception as e:
            logger.error(f"Failed to set up LangGraph agent: {e}")
            raise

    def _is_ai_chunk(self, chunk_type: Optional[str]) -> bool:
        """チャンクがAIメッセージかどうかを判定する。"""
        return chunk_type in ("ai", "AIMessageChunk")

    def _extract_text_content(self, content: Any) -> str:
        """チャンクのコンテンツからテキストを抽出する。"""
        if isinstance(content, list):
            text_parts = [
                item.get("text", "") for item in content if isinstance(item, dict) and item.get("type") == "text"
            ]
            return "".join(text_parts)
        elif content:
            return str(content)
        return ""

    def _update_tool_call_info(
        self,
        tool_calls_map: dict[str, dict[str, Any]],
        tool_call_id: str,
        tool_name: str,
        tool_args: dict[str, Any],
    ) -> None:
        """ツール呼び出し情報を更新または作成する。"""
        if tool_call_id in tool_calls_map:
            existing_info = tool_calls_map[tool_call_id]
            if tool_name:
                existing_info["tool_name"] = tool_name
            if tool_args:
                existing_info["tool_input"] = tool_args
        else:
            tool_calls_map[tool_call_id] = {
                "tool_name": tool_name or "unknown",
                "tool_input": tool_args,
                "accumulated_json": "",  # JSONデルタを蓄積（Claude/OpenAI共通）
            }

    def _extract_json_fragment(self, chunk: Any, index_to_id_map: dict[int, str]) -> tuple[str, str]:
        """チャンクからJSON断片とtool_call_idを抽出する統一メソッド。

        Claude/OpenAI両方のストリーミング形式に対応。

        Args:
            chunk: AIメッセージチャンク
            index_to_id_map: OpenAI用のindexからtool_call_idへのマッピング

        Returns:
            (json_fragment, tool_call_id)のタプル
        """
        # Claude形式: input_json_deltaをチェック
        if isinstance(getattr(chunk, "content", None), list):
            for item in chunk.content:
                if isinstance(item, dict) and item.get("type") == "input_json_delta":
                    partial_json = item.get("partial_json", "")
                    # tool_call_idは最後に登録されたもの（後で解決）
                    return partial_json, ""

        # OpenAI形式: tool_call_chunksをチェック
        if hasattr(chunk, "tool_call_chunks") and chunk.tool_call_chunks:
            for tcc in chunk.tool_call_chunks:
                if not isinstance(tcc, dict):
                    continue

                tool_call_id = tcc.get("id")
                tcc.get("name")
                args = tcc.get("args", "")
                index = tcc.get("index", 0)

                # indexからtool_call_idへのマッピングを更新
                if tool_call_id:
                    index_to_id_map[index] = tool_call_id

                # argsの断片を返す（indexを使ってtool_call_idを特定）
                if args and index in index_to_id_map:
                    return args, index_to_id_map[index]
                elif tool_call_id:
                    # argsがない場合でもtool_call_idは返す
                    return "", tool_call_id

        return "", ""

    def _process_tool_input_streaming(
        self,
        tool_calls_map: dict[str, dict[str, Any]],
        index_to_id_map: dict[int, str],
        chunk: Any,
    ) -> None:
        """ツール入力のストリーミングを処理する統一メソッド（Claude/OpenAI共通）。

        Args:
            tool_calls_map: ツール呼び出し情報のマップ
            index_to_id_map: OpenAI用のindexからtool_call_idへのマッピング
            chunk: AIメッセージチャンク
        """
        json_fragment, tool_call_id = self._extract_json_fragment(chunk, index_to_id_map)

        if not json_fragment:
            return

        # tool_call_idの決定（Claude形式の場合は最後のエントリを使用）
        if not tool_call_id and tool_calls_map:
            tool_call_id = list(tool_calls_map.keys())[-1]

        if tool_call_id and tool_call_id in tool_calls_map:
            # JSON断片を蓄積
            tool_calls_map[tool_call_id]["accumulated_json"] += json_fragment

            # パースを試みる
            try:
                parsed_input = json.loads(tool_calls_map[tool_call_id]["accumulated_json"])
                tool_calls_map[tool_call_id]["tool_input"] = parsed_input
                logger.debug(f"Parsed tool_input from JSON fragment for {tool_call_id}: {parsed_input}")
            except json.JSONDecodeError:
                # まだ完全なJSONではない
                pass

    def _get_tool_input(
        self,
        tool_calls_map: dict[str, dict[str, Any]],
        tool_call_id: str,
        chunk: Any,
    ) -> dict[str, Any]:
        """ツール入力情報を取得する。"""
        if tool_call_id and tool_call_id in tool_calls_map:
            return tool_calls_map[tool_call_id].get("tool_input", {})

        # フォールバック: chunkのartifactから取得
        if hasattr(chunk, "artifact"):
            return getattr(chunk, "artifact", {})

        return {}

    def _process_ai_chunk(
        self,
        chunk: Any,
        tool_calls_map: dict[str, dict[str, Any]],
        index_to_id_map: dict[int, str],
    ) -> tuple[str, str]:
        """AIチャンクを処理してコンテンツとメッセージタイプを返す。

        Args:
            chunk: AIメッセージチャンク
            tool_calls_map: ツール呼び出し情報のマップ
            index_to_id_map: OpenAI用のindexからtool_call_idへのマッピング

        Returns:
            (message_type, content_text)のタプル
        """
        # tool_callsを保存または更新
        if hasattr(chunk, "tool_calls") and chunk.tool_calls:
            for tool_call in chunk.tool_calls:
                tool_call_id = tool_call.get("id", "")
                if tool_call_id:
                    self._update_tool_call_info(
                        tool_calls_map,
                        tool_call_id,
                        tool_call.get("name", ""),
                        tool_call.get("args", {}),
                    )

        # ツール入力のストリーミングを処理
        self._process_tool_input_streaming(tool_calls_map, index_to_id_map, chunk)

        # コンテンツをトークン単位で返す
        content_text = self._extract_text_content(chunk.content)
        return (chunk.type, content_text)

    def _process_tool_chunk(
        self,
        chunk: Any,
        tool_calls_map: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """ツールチャンクを処理してツール情報を返す。

        Args:
            chunk: ツールメッセージチャンク
            tool_calls_map: ツール呼び出し情報のマップ

        Returns:
            ツール実行情報の辞書
        """
        tool_call_id = getattr(chunk, "tool_call_id", "")
        tool_name = getattr(chunk, "name", "unknown")
        tool_input = self._get_tool_input(tool_calls_map, tool_call_id, chunk)

        if not tool_input:
            logger.warning(f"Tool input not found for {tool_name} (ID: {tool_call_id})")

        # contentを安全に文字列化
        tool_output = self._extract_text_content(chunk.content) if hasattr(chunk, "content") else ""

        return {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output,
        }

    async def astream(
        self,
        user_input: str,
        session_id: str = "default",
    ) -> AsyncIterator[tuple[str, Any, Optional[dict[str, Any]]]]:
        """エージェント応答を非同期でストリーミングする。

        Args:
            user_input: ユーザーの入力メッセージ
            session_id: 会話コンテキストのセッションID

        Yields:
            (message_type, content, tool_info)のタプル。
            - message_typeは'ai'、'tool'など
            - tool_infoはツール実行時のみ、ツール名と入力・出力を含む辞書
        """
        if not self._agent:
            raise RuntimeError("Agent not initialized")

        try:
            logger.info(f"Processing user input: {user_input[:100]}...")
            config = {"configurable": {"thread_id": session_id}}

            # ツール呼び出し情報を一時保存 (tool_call_id -> tool_info のマッピング)
            tool_calls_map: dict[str, dict[str, Any]] = {}
            # OpenAI用: indexからtool_call_idへのマッピング
            index_to_id_map: dict[int, str] = {}

            # エージェント応答をストリーミング - トークン単位のストリーミングを取得するためにmessagesモードを使用
            async for chunk, _metadata in self._agent.astream(
                {"messages": [("user", user_input)]},
                config=config,
                stream_mode="messages",
            ):
                if not (hasattr(chunk, "type") and hasattr(chunk, "content")):
                    continue

                chunk_type = getattr(chunk, "type", None)

                # AIメッセージの場合
                if self._is_ai_chunk(chunk_type):
                    message_type, content_text = self._process_ai_chunk(chunk, tool_calls_map, index_to_id_map)
                    if content_text:
                        yield (message_type, content_text, None)

                # ツールメッセージの場合
                elif chunk.type == "tool":
                    tool_info = self._process_tool_chunk(chunk, tool_calls_map)
                    yield (chunk.type, chunk.content, tool_info)

        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            raise

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
            メッセージとその他の応答データを含む辞書
        """
        if not self._agent:
            raise RuntimeError("Agent not initialized")

        try:
            logger.info(f"Invoking agent with input: {user_input[:100]}...")
            config = {"configurable": {"thread_id": session_id}}

            result = await self._agent.ainvoke(
                {"messages": [("user", user_input)]},
                config=config,
            )

            logger.info("Agent invocation completed successfully")
            return result

        except Exception as e:
            logger.error(f"Error during invocation: {e}")
            raise
