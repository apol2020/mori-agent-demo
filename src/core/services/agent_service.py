"""チャット会話を管理するエージェントサービス。"""

from collections.abc import AsyncIterator
from typing import Optional

from src.core.agents.chat_agent import ChatAgent
from src.infrastructure.llm.anthropic_client import AnthropicClient
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AgentService:
    """エージェント会話を管理するサービス。

    このサービスはChatAgentの薄いラッパーとして機能する。
    メッセージ履歴はLangGraphのMemorySaverとStreamlitのセッション状態で管理される。
    """

    def __init__(
        self,
        model_id: str = "claude-sonnet-4-20250514",
        anthropic_client: Optional[AnthropicClient] = None,
        username: Optional[str] = None,
    ) -> None:
        """エージェントサービスを初期化する。

        Args:
            model_id: 使用するモデルID
            anthropic_client: Anthropicクライアントインスタンス（後方互換性のため）
            username: ログイン中のユーザー名（ナラティブデータのフィルタリングに使用）
        """
        self._agent = ChatAgent(model_id=model_id, anthropic_client=anthropic_client, username=username)

    async def stream_message(
        self,
        session_id: str,
        message: str,
    ) -> AsyncIterator[tuple[str, Optional[dict[str, str]]]]:
        """エージェントからメッセージ応答をストリーミングする。

        Args:
            session_id: 会話コンテキストのセッションID
            message: ユーザーメッセージ

        Yields:
            (content, tool_execution)のタプル
            - content: AIからの応答チャンク
            - tool_execution: ツール実行情報（ツール実行時のみ）
        """
        logger.info(f"Streaming message for session: {session_id}")

        # ChatAgentに直接委譲
        async for chunk, tool_execution in self._agent.astream_response(
            user_input=message,
            session_id=session_id,
        ):
            yield (chunk, tool_execution)

        logger.info("Streaming completed successfully")
