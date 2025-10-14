"""エージェント会話用のチャットインターフェースコンポーネント。"""

from typing import Optional

import streamlit as st

from src.core.models.agent_model import ChatMessage, MessageRole, ToolExecution
from src.ui.config.tool_display_config import ToolDisplayConfig
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _format_message_content(content: str) -> str:
    """メッセージコンテンツのマークダウンを適切にフォーマットする。

    Args:
        content: 元のメッセージコンテンツ

    Returns:
        フォーマット済みのメッセージコンテンツ
    """
    if not content:
        return content

    import re

    # 基本的な改行処理
    content = content.replace("\r\n", "\n").replace("\r", "\n")

    # ステップ1: マークダウン見出しの修正: # の後にスペースがない場合は追加
    # 例: "##📅" -> "## 📅", "###1." -> "### 1."
    # 見出しの連続した#記号全体を保護しながら処理
    content = re.sub(r"(#{1,6})([^\s#\n])", r"\1 \2", content)

    # ステップ2: 見出しの前に空行を追加（テキストの直後に見出しが来る場合）
    # 例: "テキスト ## 見出し" -> "テキスト\n\n## 見出し"
    # 例: "テキスト\n## 見出し" -> "テキスト\n\n## 見出し"
    # 例: "テキスト### 見出し" -> "テキスト\n\n### 見出し"
    # 改行でない文字の直後に見出しが来る場合（スペースあり/なし）
    content = re.sub(r"([^\n#])(#{1,6}\s+)", r"\1\n\n\2", content)
    # 改行1つの後に見出しが来る場合（空行でない場合）
    content = re.sub(r"([^\n])\n(#{1,6}\s+)", r"\1\n\n\2", content)

    # ステップ3: 見出しの後に空行を追加（見出しの直後にテキストが来る場合）
    # 例: "## 見出し\nテキスト" -> "## 見出し\n\nテキスト"
    # ただし、次の行が別の見出しやリストの場合は除外
    content = re.sub(r"(#{1,6}\s+[^\n]+)\n(?!\n|#{1,6}|[-*+]\s|\d+\.)", r"\1\n\n", content)

    # ステップ4: リストアイテムの前に改行を確保
    # 例: "項目- リスト" -> "項目\n- リスト"
    content = re.sub(r"([^\n])([-*+]\s+)", r"\1\n\2", content)

    # ステップ5: 通常の文章の後のリストの前に空行を追加
    # コロンや見出し直後のリストは除外
    content = re.sub(r"([^\n:：])\n([-*+]\s+)", r"\1\n\n\2", content)

    # ステップ6: 複数の連続する空行を2つまでに制限
    content = re.sub(r"\n{3,}", "\n\n", content)

    return content


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
                # 改行と段落分けを適切に処理するため、内容を前処理
                formatted_content = _format_message_content(part.content)
                # マークダウンとして処理
                st.markdown(formatted_content)
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
