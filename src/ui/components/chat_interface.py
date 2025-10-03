"""エージェント会話用のチャットインターフェースコンポーネント。"""

from typing import Optional

import streamlit as st

from src.core.models.agent_model import ChatMessage, MessageRole, ToolExecution
from src.ui.config.tool_display_config import ToolDisplayConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


def render_tool_execution(tool_execution: ToolExecution) -> None:
    """ツール実行情報をエクスパンダーで表示する。

    表示設定はToolDisplayConfigから取得される。

    Args:
        tool_execution: ツール実行情報
    """
    tool_name = tool_execution.tool_name

    # 設定を取得
    icon = ToolDisplayConfig.get_icon(tool_name)
    expanded = ToolDisplayConfig.get_expanded(tool_name)
    input_label = ToolDisplayConfig.get_input_label(tool_name)
    output_label = ToolDisplayConfig.get_output_label(tool_name)
    input_language = ToolDisplayConfig.get_input_language(tool_name)
    output_language = ToolDisplayConfig.get_output_language(tool_name)
    show_timestamp = ToolDisplayConfig.get_show_timestamp(tool_name)
    timestamp_format = ToolDisplayConfig.get_timestamp_format(tool_name)

    # エクスパンダーで表示
    with st.expander(f"{icon} ツール実行: {tool_name}", expanded=expanded):
        st.markdown(input_label)
        st.code(tool_execution.input_data, language=input_language)
        st.markdown(output_label)
        st.code(tool_execution.output_data, language=output_language)
        if show_timestamp:
            st.caption(f"実行時刻: {tool_execution.timestamp.strftime(timestamp_format)}")


def render_chat_message(message: ChatMessage) -> None:
    """単一のチャットメッセージをレンダリングする。"""
    role_name_map = {
        MessageRole.USER: "user",
        MessageRole.ASSISTANT: "assistant",
        MessageRole.SYSTEM: "system",
    }

    with st.chat_message(role_name_map[message.role]):
        for part in message.parts:
            if part.type == "text":
                st.markdown(part.content)
            elif part.type == "tool":
                render_tool_execution(part.tool_execution)


def render_chat_history(messages: list[ChatMessage]) -> None:
    """チャット履歴をレンダリングする。"""
    for message in messages:
        render_chat_message(message)


def render_chat_input(
    key: str = "chat_input",
    placeholder: str = "メッセージを入力してください...",
) -> Optional[str]:
    """チャット入力をレンダリングしてユーザーのメッセージを返す。"""
    result = st.chat_input(placeholder, key=key)
    return result if result else None


def render_chat_controls(use_container_width: bool = True) -> dict:
    """チャットコントロールボタンをレンダリングして状態を返す。

    Args:
        use_container_width: コンテナ幅全体を使用するかどうか

    Returns:
        ボタン状態の辞書
    """
    new_session = st.button(
        "🆕 新しい会話を始める",
        help="新しい会話を開始します",
        use_container_width=use_container_width,
    )

    export_chat = st.button(
        "💾 エクスポート",
        help="会話履歴をエクスポートします",
        use_container_width=use_container_width,
    )

    return {
        "new_session": new_session,
        "export_chat": export_chat,
    }


def render_error_message(error: str) -> None:
    """エラーメッセージをレンダリングする。"""
    st.error(f"⚠️ エラー: {error}")
