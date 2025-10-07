"""ツール実行表示のUI設定。"""

from typing import Any, Optional


class ToolDisplayConfig:
    """ツール実行表示の設定を管理するクラス。"""

    # デフォルト設定
    DEFAULT_ICON = "🔧"
    DEFAULT_EXPANDED = False
    DEFAULT_INPUT_LABEL = "**入力:**"
    DEFAULT_OUTPUT_LABEL = "**出力:**"
    DEFAULT_INPUT_LANGUAGE = "json"
    DEFAULT_OUTPUT_LANGUAGE = "text"
    DEFAULT_SHOW_TIMESTAMP = True
    DEFAULT_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"

    # ツール別カスタム設定
    TOOL_CONFIGS: dict[str, dict[str, Any]] = {
        "get_current_time": {
            "icon": "⏰",
            "input_language": "text",
            "output_language": "text",
        },
    }

    @classmethod
    def get_icon(cls, tool_name: str) -> str:
        """ツールのアイコンを取得する。

        Args:
            tool_name: ツール名

        Returns:
            アイコン文字列
        """
        config = cls.TOOL_CONFIGS.get(tool_name, {})
        return str(config.get("icon", cls.DEFAULT_ICON))

    @classmethod
    def get_expanded(cls, tool_name: str) -> bool:
        """エクスパンダーの初期展開状態を取得する。

        Args:
            tool_name: ツール名

        Returns:
            展開状態（True=展開、False=折りたたみ）
        """
        config = cls.TOOL_CONFIGS.get(tool_name, {})
        expanded = config.get("expanded", cls.DEFAULT_EXPANDED)
        return bool(expanded)

    @classmethod
    def get_input_label(cls, tool_name: str) -> str:
        """入力ラベルを取得する。

        Args:
            tool_name: ツール名

        Returns:
            入力ラベル文字列
        """
        config = cls.TOOL_CONFIGS.get(tool_name, {})
        return str(config.get("input_label", cls.DEFAULT_INPUT_LABEL))

    @classmethod
    def get_output_label(cls, tool_name: str) -> str:
        """出力ラベルを取得する。

        Args:
            tool_name: ツール名

        Returns:
            出力ラベル文字列
        """
        config = cls.TOOL_CONFIGS.get(tool_name, {})
        return str(config.get("output_label", cls.DEFAULT_OUTPUT_LABEL))

    @classmethod
    def get_input_language(cls, tool_name: str) -> str:
        """入力表示用の言語設定を取得する。

        Args:
            tool_name: ツール名

        Returns:
            言語設定（例: "json", "text", "python"）
        """
        config = cls.TOOL_CONFIGS.get(tool_name, {})
        return str(config.get("input_language", cls.DEFAULT_INPUT_LANGUAGE))

    @classmethod
    def get_output_language(cls, tool_name: str) -> str:
        """出力表示用の言語設定を取得する。

        Args:
            tool_name: ツール名

        Returns:
            言語設定（例: "json", "text", "python"）
        """
        config = cls.TOOL_CONFIGS.get(tool_name, {})
        return str(config.get("output_language", cls.DEFAULT_OUTPUT_LANGUAGE))

    @classmethod
    def get_show_timestamp(cls, tool_name: str) -> bool:
        """タイムスタンプ表示の有無を取得する。

        Args:
            tool_name: ツール名

        Returns:
            タイムスタンプを表示するかどうか
        """
        config = cls.TOOL_CONFIGS.get(tool_name, {})
        show_timestamp = config.get("show_timestamp", cls.DEFAULT_SHOW_TIMESTAMP)
        return bool(show_timestamp)

    @classmethod
    def get_timestamp_format(cls, tool_name: str) -> str:
        """タイムスタンプのフォーマットを取得する。

        Args:
            tool_name: ツール名

        Returns:
            タイムスタンプのフォーマット文字列
        """
        config = cls.TOOL_CONFIGS.get(tool_name, {})
        return str(config.get("timestamp_format", cls.DEFAULT_TIMESTAMP_FORMAT))

    @classmethod
    def register_tool_config(
        cls,
        tool_name: str,
        icon: Optional[str] = None,
        expanded: Optional[bool] = None,
        input_label: Optional[str] = None,
        output_label: Optional[str] = None,
        input_language: Optional[str] = None,
        output_language: Optional[str] = None,
        show_timestamp: Optional[bool] = None,
        timestamp_format: Optional[str] = None,
    ) -> None:
        """新しいツールの表示設定を登録する。

        Args:
            tool_name: ツール名
            icon: アイコン文字列
            expanded: 初期展開状態
            input_label: 入力ラベル
            output_label: 出力ラベル
            input_language: 入力表示用言語設定
            output_language: 出力表示用言語設定
            show_timestamp: タイムスタンプ表示の有無
            timestamp_format: タイムスタンプのフォーマット
        """
        config: dict[str, Any] = {}

        if icon is not None:
            config["icon"] = icon
        if expanded is not None:
            config["expanded"] = expanded
        if input_label is not None:
            config["input_label"] = input_label
        if output_label is not None:
            config["output_label"] = output_label
        if input_language is not None:
            config["input_language"] = input_language
        if output_language is not None:
            config["output_language"] = output_language
        if show_timestamp is not None:
            config["show_timestamp"] = show_timestamp
        if timestamp_format is not None:
            config["timestamp_format"] = timestamp_format

        cls.TOOL_CONFIGS[tool_name] = config
