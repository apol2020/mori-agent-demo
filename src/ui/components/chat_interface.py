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

    # ステップ0: 意図的なマークダウンを保護し、不要な記号を削除
    # 0-1: 意図的な太字・斜体を一時的に保護
    content = re.sub(r"\*\*([^\*\n]+?)\*\*", r"__PRESERVE_BOLD__\1__PRESERVE_BOLD__", content)
    content = re.sub(r"\*([^\*\n]+?)\*", r"__PRESERVE_ITALIC__\1__PRESERVE_ITALIC__", content)

    # 0-2: 行頭のリストマーカー（* - +）を保護
    content = re.sub(r"^(\s*)([\*\-\+])(\s+)", r"\1__LIST_\2__\3", content, flags=re.MULTILINE)

    # 0-3: 不要なアスタリスクの削除
    # 句読点の前後の * を削除
    content = re.sub(r"\*([？。！、，])", r"\1", content)
    content = re.sub(r"([？。！、，])\*", r"\1", content)
    # 行末の単独 * を削除
    content = re.sub(r"\*\s*$", "", content, flags=re.MULTILINE)

    # 0-4: 不要なハイフンの削除（慎重に）
    # 句読点の直後のハイフン（ただし次が数字でない場合のみ）
    content = re.sub(r"([？。！])-(?!\d)", r"\1", content)
    # 行末の単独ハイフン（スペースの後のみ）
    content = re.sub(r"\s+-\s*$", "", content, flags=re.MULTILINE)

    # 0-5: 残った単独の * はそのまま残す（保護済みの太字は復元される）
    # エスケープしない（Streamlitのマークダウンレンダラーに任せる）

    # 0-6: 保護したリストマーカーのみを復元（太字・斜体は後で復元）
    content = content.replace("__LIST_*__", "*")
    content = content.replace("__LIST_-__", "-")
    content = content.replace("__LIST_+__", "+")

    # ステップ1: 絵文字の後の処理
    # 絵文字の後にゼロ幅スペースを追加してマークダウン誤解釈を防ぐ
    emoji_pattern = r"([\U0001F300-\U0001F9FF\u2600-\u26FF\u2700-\u27BF])\s*"
    zero_width_space = "\u200b"
    content = re.sub(emoji_pattern, r"\1" + zero_width_space + " ", content)

    # ステップ2: マークダウン見出しの修正
    content = re.sub(r"(#{1,6})([^\s#\n])", r"\1 \2", content)
    content = re.sub(r"([^\n#])(#{1,6}\s+)", r"\1\n\n\2", content)
    content = re.sub(r"([^\n])\n(#{1,6}\s+)", r"\1\n\n\2", content)

    # 2-5: 見出しに説明文が含まれている場合は分割
    # 「### 店舗名 説明文...」→「### 店舗名\n\n説明文...」
    # カタカナ・漢字の店舗名の後にひらがな・漢字の説明文が続く場合
    content = re.sub(
        r"(#{1,6}\s+)([\u30A0-\u30FF\u4E00-\u9FFF\w]+)\s+([ぁ-んァ-ヶ\u4E00-\u9FFF].{10,})", r"\1\2\n\n\3", content
    )

    content = re.sub(r"(#{1,6}\s+[^\n]+)\n(?!\n|#{1,6}|[-*+]\s|\d+\.)", r"\1\n\n", content)

    # ステップ3: リストアイテムの処理
    list_markers = r"[-*+・]"

    # 3-1: 連続リストマーカーを削除
    content = re.sub(rf"({list_markers}){{2,}}", r"\1", content)

    # 3-2: 行頭以外の `-` を強制的に改行（改良版）
    # 「場所: xxx - 営業時間: xxx」や「場所: xxx- 営業時間: xxx」を改行
    # `-` の前後にスペースがあってもなくても対応
    content = re.sub(r"([^\n])\s*-\s+([^\s\n-])", r"\1\n- \2", content)

    # 3-3: リストマーカー直後にスペース追加（ただし太字の**は除外）
    content = re.sub(rf"^(\s*)({list_markers})(?!\*)([^\s])", r"\1\2 \3", content, flags=re.MULTILINE)

    # 3-4: リスト前に空行追加（コロンの後は除く）
    content = re.sub(rf"([^\n:：])\n({list_markers}\s+)", r"\1\n\n\2", content)

    # ステップ4: 長文の改行処理
    # 句読点の後に100文字以上続く場合、改行を追加
    content = re.sub(r"([。！？])([^\n。！？]{100,})", r"\1\n\n\2", content)

    # ステップ5: データ項目の改行
    content = re.sub(r"(:[^\n]*?[0-9a-zA-Z\-\./]+)([ぁ-んー]{2,})", r"\1\n\n\2", content)

    # ステップ6: 不要なコロンの削除
    content = re.sub(rf"([^例注備考メモヒント参考])[：:]\s*\n({list_markers}\s+)", r"\1\n\2", content)

    # ステップ7: 連続空行を制限
    content = re.sub(r"\n{3,}", "\n\n", content)

    # ステップ8: 最後に保護した太字・斜体を復元
    content = content.replace("__PRESERVE_BOLD__", "**")
    content = content.replace("__PRESERVE_ITALIC__", "*")

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
