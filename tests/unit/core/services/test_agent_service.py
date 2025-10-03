"""AgentServiceのユニットテスト。"""

from collections.abc import AsyncIterator
from unittest.mock import MagicMock, patch

import pytest

from src.core.services.agent_service import AgentService


@pytest.mark.asyncio
class TestAgentService:
    """AgentServiceのテスト。"""

    async def test_agent_service_initialization(self) -> None:
        """AgentServiceが正しく初期化されることを確認。"""
        with patch("src.core.services.agent_service.ChatAgent"):
            service = AgentService()
            assert service is not None
            assert hasattr(service, "_agent")

    async def test_agent_service_with_custom_client(self) -> None:
        """カスタムAnthropicクライアントでAgentServiceを初期化できることを確認。"""
        mock_client = MagicMock()
        with patch("src.core.services.agent_service.ChatAgent"):
            service = AgentService(anthropic_client=mock_client)
            assert service is not None

    async def test_stream_message_yields_chunks(self) -> None:
        """stream_messageがチャンクをyieldすることを確認。"""
        mock_agent = MagicMock()

        async def mock_astream(user_input: str, session_id: str) -> AsyncIterator[tuple[str, None]]:
            yield ("Hello ", None)
            yield ("World", None)

        mock_agent.astream_response = mock_astream

        with patch("src.core.services.agent_service.ChatAgent", return_value=mock_agent):
            service = AgentService()

            chunks = []
            async for chunk, _tool_exec in service.stream_message(session_id="test_session", message="Hi"):
                chunks.append(chunk)

            assert len(chunks) == 2
            assert chunks[0] == "Hello "
            assert chunks[1] == "World"

    async def test_stream_message_with_session_id(self) -> None:
        """stream_messageがsession_idを正しく渡すことを確認。"""
        received_session_id = None
        received_user_input = None

        async def mock_astream(user_input: str, session_id: str) -> AsyncIterator[tuple[str, None]]:
            nonlocal received_session_id, received_user_input
            received_session_id = session_id
            received_user_input = user_input
            yield ("Response", None)

        mock_agent = MagicMock()
        mock_agent.astream_response = mock_astream

        with patch("src.core.services.agent_service.ChatAgent", return_value=mock_agent):
            service = AgentService()

            chunks = []
            async for chunk, _tool_exec in service.stream_message(session_id="custom_session", message="Test message"):
                chunks.append(chunk)

            # astream_responseが正しい引数で呼び出されたことを確認
            assert received_session_id == "custom_session"
            assert received_user_input == "Test message"

    async def test_stream_message_handles_exception(self) -> None:
        """stream_message中の例外が正しく伝播されることを確認。"""

        async def mock_astream_error(user_input: str, session_id: str) -> AsyncIterator[tuple[str, None]]:
            raise Exception("Test error")
            yield  # この行は実行されない

        mock_agent = MagicMock()
        mock_agent.astream_response = mock_astream_error

        with patch("src.core.services.agent_service.ChatAgent", return_value=mock_agent):
            service = AgentService()

            # 例外が伝播されることを確認（エラーハンドリングはChatAgentの責任）
            with pytest.raises(Exception, match="Test error"):
                async for _chunk, _tool_exec in service.stream_message(session_id="test", message="Hi"):
                    pass

    async def test_stream_message_empty_response(self) -> None:
        """空のレスポンスが正しく処理されることを確認。"""

        async def mock_astream(user_input: str, session_id: str) -> AsyncIterator[tuple[str, None]]:
            # 空のイテレータ
            return
            yield  # この行は実行されない

        mock_agent = MagicMock()
        mock_agent.astream_response = mock_astream

        with patch("src.core.services.agent_service.ChatAgent", return_value=mock_agent):
            service = AgentService()

            chunks = []
            async for chunk, _tool_exec in service.stream_message(session_id="test", message="Hi"):
                chunks.append(chunk)

            assert len(chunks) == 0

    async def test_stream_message_multiple_chunks(self) -> None:
        """複数のチャンクが順番にyieldされることを確認。"""

        async def mock_astream(user_input: str, session_id: str) -> AsyncIterator[tuple[str, None]]:
            for i in range(5):
                yield (f"chunk{i} ", None)

        mock_agent = MagicMock()
        mock_agent.astream_response = mock_astream

        with patch("src.core.services.agent_service.ChatAgent", return_value=mock_agent):
            service = AgentService()

            chunks = []
            async for chunk, _tool_exec in service.stream_message(session_id="test", message="Hi"):
                chunks.append(chunk)

            assert len(chunks) == 5
            for i in range(5):
                assert chunks[i] == f"chunk{i} "

    async def test_stream_message_with_unicode(self) -> None:
        """Unicode文字を含むメッセージが正しく処理されることを確認。"""

        async def mock_astream(user_input: str, session_id: str) -> AsyncIterator[tuple[str, None]]:
            yield ("こんにちは", None)
            yield ("世界", None)

        mock_agent = MagicMock()
        mock_agent.astream_response = mock_astream

        with patch("src.core.services.agent_service.ChatAgent", return_value=mock_agent):
            service = AgentService()

            chunks = []
            async for chunk, _tool_exec in service.stream_message(session_id="test", message="テスト"):
                chunks.append(chunk)

            assert len(chunks) == 2
            assert chunks[0] == "こんにちは"
            assert chunks[1] == "世界"
