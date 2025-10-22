"""ツールの基底クラス。"""

import json
from abc import ABC, abstractmethod
from datetime import date, datetime
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

    def _json_serializer(self, obj: Any) -> str:
        """JSON非対応の型を文字列に変換するヘルパー。

        Args:
            obj: 変換対象のオブジェクト

        Returns:
            ISO形式の文字列（datetime/date）または文字列表現
        """
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return str(obj)

    def format_input(self, **kwargs: Any) -> str:
        """ツールの入力をフォーマットする。

        Args:
            **kwargs: ツール実行時の入力パラメータ

        Returns:
            フォーマットされた入力文字列（デフォルトはJSON形式）
        """
        try:
            return json.dumps(kwargs, ensure_ascii=False, indent=2, default=self._json_serializer)
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
                return json.dumps(output, ensure_ascii=False, indent=2, default=self._json_serializer)
            except Exception:
                return str(output)
        return str(output)
