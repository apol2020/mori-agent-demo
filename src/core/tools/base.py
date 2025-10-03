"""ツールの基底クラス。"""

import json
from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """すべてのツールの基底クラス。"""

    @property
    @abstractmethod
    def name(self) -> str:
        """ツール名。"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """ツールの説明。"""
        pass

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """指定されたパラメータでツールを実行する。"""
        pass

    def format_input(self, **kwargs: Any) -> str:
        """ツールの入力をフォーマットする。

        Args:
            **kwargs: ツール実行時の入力パラメータ

        Returns:
            フォーマットされた入力文字列（デフォルトはJSON形式）
        """
        try:
            return json.dumps(kwargs, ensure_ascii=False, indent=2)
        except Exception:
            return str(kwargs)

    def format_output(self, output: Any) -> str:
        """ツールの出力をフォーマットする。

        Args:
            output: ツール実行結果

        Returns:
            フォーマットされた出力文字列
        """
        if isinstance(output, (dict, list)):
            try:
                return json.dumps(output, ensure_ascii=False, indent=2)
            except Exception:
                return str(output)
        return str(output)
