"""ChatAgentのユニットテスト。"""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.agents.chat_agent import ChatAgent


class TestChatAgent:
    """ChatAgentのテスト。"""

    def test_chat_agent_initialization(self) -> None:
        """ChatAgentが正しく初期化されることを確認。"""
        with patch("src.core.agents.chat_agent.AnthropicClient"), patch("src.core.agents.chat_agent.LangChainAdapter"):
            agent = ChatAgent()
            assert agent is not None
            assert hasattr(agent, "_tools")
            assert hasattr(agent, "_tool_instances")
            assert hasattr(agent, "_adapter")
            assert hasattr(agent, "_output_normalizer")

    def test_chat_agent_initialization_with_custom_model(self) -> None:
        """カスタムモデルIDでChatAgentを初期化できることを確認。"""
        with (
            patch("src.core.agents.chat_agent.LangChainAdapter"),
            patch("src.infrastructure.llm.llm_factory.create_llm"),
        ):
            agent = ChatAgent(model_id="gpt-5")
            assert agent is not None
            assert hasattr(agent, "_adapter")

    def test_create_tools_returns_list(self) -> None:
        """ツールレジストリからツールが正しくロードされることを確認。"""
        with patch("src.core.agents.chat_agent.AnthropicClient"), patch("src.core.agents.chat_agent.LangChainAdapter"):
            agent = ChatAgent()
            tools = agent._tools
            assert isinstance(tools, list)
            assert len(tools) == 2

    def test_create_tools_contains_time_tool(self) -> None:
        """ツールレジストリがtime toolを含むことを確認。"""
        with patch("src.core.agents.chat_agent.AnthropicClient"), patch("src.core.agents.chat_agent.LangChainAdapter"):
            agent = ChatAgent()
            tools = agent._tools
            tool_names = [tool.name for tool in tools]
            assert "get_current_time" in tool_names

    def test_create_tools_contains_multiply_tool(self) -> None:
        """ツールレジストリがmultiply toolを含むことを確認。"""
        with patch("src.core.agents.chat_agent.AnthropicClient"), patch("src.core.agents.chat_agent.LangChainAdapter"):
            agent = ChatAgent()
            tools = agent._tools
            tool_names = [tool.name for tool in tools]
            assert "multiply" in tool_names

    @pytest.mark.asyncio
    async def test_astream_response_yields_content(self) -> None:
        """astream_responseがコンテンツをyieldすることを確認。"""
        mock_adapter = MagicMock()

        async def mock_astream(user_input: str, session_id: str) -> AsyncIterator[tuple[str, str, None]]:
            yield ("ai", "Hello ", None)
            yield ("ai", "World", None)

        mock_adapter.astream = mock_astream

        with (
            patch("src.core.agents.chat_agent.AnthropicClient"),
            patch("src.core.agents.chat_agent.LangChainAdapter", return_value=mock_adapter),
        ):
            agent = ChatAgent()
            agent._adapter = mock_adapter

            chunks = []
            async for content, _tool_exec in agent.astream_response(user_input="Hi", session_id="test"):
                chunks.append(content)

            assert len(chunks) == 2
            assert chunks[0] == "Hello "
            assert chunks[1] == "World"

    @pytest.mark.asyncio
    async def test_astream_response_filters_non_ai_messages(self) -> None:
        """astream_responseがAI以外のメッセージをフィルタすることを確認。"""
        mock_adapter = MagicMock()

        async def mock_astream(user_input: str, session_id: str) -> AsyncIterator[tuple[str, str, None]]:
            yield ("system", "System message", None)
            yield ("ai", "AI response", None)
            yield ("tool", "Tool output", None)

        mock_adapter.astream = mock_astream

        with (
            patch("src.core.agents.chat_agent.AnthropicClient"),
            patch("src.core.agents.chat_agent.LangChainAdapter", return_value=mock_adapter),
        ):
            agent = ChatAgent()
            agent._adapter = mock_adapter

            chunks = []
            async for content, _tool_exec in agent.astream_response(user_input="Hi", session_id="test"):
                chunks.append(content)

            # AI メッセージのみが返される
            assert len(chunks) == 1
            assert chunks[0] == "AI response"

    @pytest.mark.asyncio
    async def test_astream_response_handles_empty_content(self) -> None:
        """astream_responseが空のコンテンツを処理することを確認。"""
        mock_adapter = MagicMock()

        async def mock_astream(user_input: str, session_id: str) -> AsyncIterator[tuple[str, str, None]]:
            yield ("ai", "", None)
            yield ("ai", "Valid content", None)
            yield ("ai", "", None)

        mock_adapter.astream = mock_astream

        with (
            patch("src.core.agents.chat_agent.AnthropicClient"),
            patch("src.core.agents.chat_agent.LangChainAdapter", return_value=mock_adapter),
        ):
            agent = ChatAgent()
            agent._adapter = mock_adapter

            chunks = []
            async for content, _tool_exec in agent.astream_response(user_input="Hi", session_id="test"):
                chunks.append(content)

            # 空のコンテンツはスキップされる
            assert len(chunks) == 1
            assert chunks[0] == "Valid content"

    @pytest.mark.asyncio
    async def test_astream_response_handles_exception(self) -> None:
        """astream_response中の例外が正しく処理されることを確認。"""
        mock_adapter = MagicMock()

        async def mock_astream_error(user_input: str, session_id: str) -> AsyncIterator[tuple[str, str, None]]:
            raise Exception("Test error")
            yield  # この行は実行されない

        mock_adapter.astream = mock_astream_error

        with (
            patch("src.core.agents.chat_agent.AnthropicClient"),
            patch("src.core.agents.chat_agent.LangChainAdapter", return_value=mock_adapter),
        ):
            agent = ChatAgent()
            agent._adapter = mock_adapter

            chunks = []
            async for content, _tool_exec in agent.astream_response(user_input="Hi", session_id="test"):
                chunks.append(content)

            assert len(chunks) == 1
            assert "エラー" in chunks[0]
            assert "Test error" in chunks[0]

    @pytest.mark.asyncio
    async def test_ainvoke_returns_dict(self) -> None:
        """ainvokeが辞書を返すことを確認。"""
        mock_adapter = MagicMock()
        mock_message = MagicMock()
        mock_message.type = "ai"
        mock_message.content = "AI response"
        mock_adapter.ainvoke = AsyncMock(return_value={"messages": [mock_message]})

        with (
            patch("src.core.agents.chat_agent.AnthropicClient"),
            patch("src.core.agents.chat_agent.LangChainAdapter", return_value=mock_adapter),
        ):
            agent = ChatAgent()
            agent._adapter = mock_adapter

            result = await agent.ainvoke(user_input="Hi", session_id="test")

            assert isinstance(result, dict)
            assert "output" in result
            assert "messages" in result

    @pytest.mark.asyncio
    async def test_ainvoke_extracts_output(self) -> None:
        """ainvokeが出力を正しく抽出することを確認。"""
        mock_adapter = MagicMock()
        mock_message = MagicMock()
        mock_message.type = "ai"
        mock_message.content = "Expected output"
        mock_adapter.ainvoke = AsyncMock(return_value={"messages": [mock_message]})

        with (
            patch("src.core.agents.chat_agent.AnthropicClient"),
            patch("src.core.agents.chat_agent.LangChainAdapter", return_value=mock_adapter),
        ):
            agent = ChatAgent()
            agent._adapter = mock_adapter

            result = await agent.ainvoke(user_input="Hi", session_id="test")

            assert result["output"] == "Expected output"

    @pytest.mark.asyncio
    async def test_ainvoke_handles_exception(self) -> None:
        """ainvoke中の例外が正しく処理されることを確認。"""
        mock_adapter = MagicMock()
        mock_adapter.ainvoke = AsyncMock(side_effect=Exception("Test error"))

        with (
            patch("src.core.agents.chat_agent.AnthropicClient"),
            patch("src.core.agents.chat_agent.LangChainAdapter", return_value=mock_adapter),
        ):
            agent = ChatAgent()
            agent._adapter = mock_adapter

            result = await agent.ainvoke(user_input="Hi", session_id="test")

            assert "エラー" in result["output"]
            assert "Test error" in result["output"]
            assert result["messages"] == []

    @pytest.mark.asyncio
    async def test_astream_response_with_different_session_ids(self) -> None:
        """異なるsession_idでastream_responseが動作することを確認。"""
        call_count = 0

        async def mock_astream(user_input: str, session_id: str) -> AsyncIterator[tuple[str, str, None]]:
            nonlocal call_count
            call_count += 1
            yield ("ai", "Response", None)

        mock_adapter = MagicMock()
        mock_adapter.astream = mock_astream

        with (
            patch("src.core.agents.chat_agent.AnthropicClient"),
            patch("src.core.agents.chat_agent.LangChainAdapter", return_value=mock_adapter),
        ):
            agent = ChatAgent()
            agent._adapter = mock_adapter

            # 異なるsession_idで複数回呼び出し
            async for _ in agent.astream_response(user_input="Hi", session_id="session1"):
                pass
            async for _ in agent.astream_response(user_input="Hello", session_id="session2"):
                pass

            assert call_count == 2
