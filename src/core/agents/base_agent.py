"""エージェント実装の基底インターフェース。"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, Optional


class BaseAgent(ABC):
    """エージェント実装の抽象基底クラス。

    このインターフェースは、すべてのエージェント実装が従うべき契約を定義し、
    コアレイヤーでフレームワークに依存しないビジネスロジックを可能にする。
    """

    @abstractmethod
    def astream_response(
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
        """
        raise NotImplementedError

    @abstractmethod
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
        pass
