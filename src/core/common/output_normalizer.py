"""エージェント応答の出力正規化ユーティリティ。"""

from typing import Any

from src.utils.logger import get_logger

logger = get_logger(__name__)


class OutputNormalizer:
    """エージェント出力を一貫した文字列形式に正規化する。

    このユーティリティは、異なるエージェント実装からの様々な出力形式を処理し、
    標準的な文字列表現に正規化する。
    """

    @staticmethod
    def normalize(output: Any) -> str:
        """エージェント出力を文字列形式に正規化する。

        Args:
            output: エージェントからの出力（str、dict、list、その他の型）

        Returns:
            正規化された文字列出力
        """
        if isinstance(output, str):
            return output

        if isinstance(output, list):
            # メッセージチャンクのリストからテキストを抽出
            text_content = ""
            for item in output:
                if isinstance(item, dict):
                    # 辞書アイテムを処理
                    if "text" in item:
                        text_content += item["text"]
                    elif "content" in item:
                        text_content += item["content"]
                elif isinstance(item, str):
                    text_content += item
            return text_content

        if isinstance(output, dict):
            # 単一の辞書出力を処理
            if "text" in output:
                return str(output["text"])
            if "content" in output:
                return str(output["content"])
            return str(output)

        # その他の型の場合は文字列に変換
        return str(output)
