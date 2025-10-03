"""数学関連ツール。"""

from typing import Any

from src.core.tools.base import BaseTool
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MultiplyTool(BaseTool):
    """二つの数値を掛け算するツール。"""

    @property
    def name(self) -> str:
        """ツール名。"""
        return "multiply"

    @property
    def description(self) -> str:
        """ツールの説明。"""
        return "二つの数値を掛け算します。a: 最初の数値, b: 二番目の数値"

    def execute(self, a: int, b: int) -> int:  # type: ignore[override]
        """二つの数値を掛け算する。

        Args:
            a: 最初の数値
            b: 二番目の数値

        Returns:
            掛け算の結果
        """
        result = a * b
        logger.debug(f"Multiply: {a} * {b} = {result}")
        return result

    def format_input(self, **kwargs: Any) -> str:
        """ツールの入力をフォーマットする（カスタム実装）。"""
        a = kwargs.get("a", "?")
        b = kwargs.get("b", "?")
        return f"{a} × {b}"

    def format_output(self, output: Any) -> str:
        """ツールの出力をフォーマットする（カスタム実装）。"""
        return f"計算結果: {output}"
