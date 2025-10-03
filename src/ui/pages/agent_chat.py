"""AI会話用のエージェントチャットページ。"""

import asyncio
import json
import uuid
from datetime import datetime

import streamlit as st

from src.config.settings import settings
from src.core.models.agent_model import ChatMessage, MessageRole
from src.core.services.agent_service import AgentService
from src.ui.components.chat_interface import (
    render_chat_history,
    render_chat_input,
    render_error_message,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _should_reset_session(selected_model: str) -> bool:
    """セッションをリセットすべきかを判定する。

    Args:
        selected_model: 選択されたモデルID

    Returns:
        セッションをリセットすべきならTrue
    """
    return "current_model" not in st.session_state or st.session_state.current_model != selected_model


def _reset_session(selected_model: str) -> None:
    """セッションをリセットする。

    Args:
        selected_model: 選択されたモデルID
    """
    st.session_state.agent_service = AgentService(model_id=selected_model)
    st.session_state.current_model = selected_model
    st.session_state.current_session_id = str(uuid.uuid4())
    st.session_state.chat_messages = []
    logger.info(f"モデルを {selected_model} に変更し、新しいセッションを開始: {st.session_state.current_session_id}")


def initialize_session_state(selected_model: str) -> None:
    """セッション状態変数を初期化する。

    Args:
        selected_model: 選択されたモデルID
    """
    # モデルが変更された場合はセッションをリセット
    if _should_reset_session(selected_model):
        _reset_session(selected_model)

    # 必要な状態変数を初期化
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = str(uuid.uuid4())
        logger.info(f"新しいセッションを作成: {st.session_state.current_session_id}")

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    if "is_processing" not in st.session_state:
        st.session_state.is_processing = False


def start_new_session() -> None:
    """新しいチャットセッションを開始する。"""
    st.session_state.current_session_id = str(uuid.uuid4())
    st.session_state.chat_messages = []
    logger.info(f"新しいセッションを開始しました: {st.session_state.current_session_id}")
    st.success(f"新しいセッションを開始しました: {st.session_state.current_session_id[:8]}...")


def _display_user_message(user_input: str) -> ChatMessage:
    """ユーザーメッセージを表示してセッション状態に追加する。

    Args:
        user_input: ユーザーの入力メッセージ

    Returns:
        作成されたユーザーメッセージ
    """
    from src.core.models.agent_model import TextPart

    user_message = ChatMessage(
        role=MessageRole.USER,
        timestamp=datetime.now(),
        parts=[TextPart(content=user_input)],
    )
    st.session_state.chat_messages.append(user_message)

    with st.chat_message("user"):
        st.markdown(user_input)

    return user_message


async def _stream_assistant_response(user_input: str) -> list:
    """アシスタント応答をストリーミングして表示する。

    Args:
        user_input: ユーザーの入力メッセージ

    Returns:
        メッセージパーツのリスト
    """
    from src.core.models.agent_model import MessagePart, TextPart, ToolExecution, ToolPart
    from src.ui.components.chat_interface import render_tool_execution

    parts: list[MessagePart] = []
    current_text = ""

    # 現在表示中のテキスト用コンテナ
    text_container = st.container()
    text_placeholder = text_container.empty()

    async for chunk, tool_execution in st.session_state.agent_service.stream_message(
        session_id=st.session_state.current_session_id,
        message=user_input,
    ):
        if chunk:
            current_text += chunk
            text_placeholder.markdown(current_text + "▌")

        if tool_execution:
            # ツール実行前のテキストを確定
            if current_text:
                text_placeholder.markdown(current_text)
                parts.append(TextPart(content=current_text))
                current_text = ""

            # ツール実行を追加
            tool_exec = ToolExecution(
                tool_name=tool_execution["tool_name"],
                input_data=tool_execution["input_data"],
                output_data=tool_execution["output_data"],
            )
            parts.append(ToolPart(tool_execution=tool_exec))

            # ツール実行を表示
            tool_container = st.container()
            with tool_container:
                render_tool_execution(tool_exec)

            # 次のテキスト用に新しいコンテナとプレースホルダーを作成
            text_container = st.container()
            text_placeholder = text_container.empty()

    # 最後のテキストパートを確定
    if current_text:
        text_placeholder.markdown(current_text)
        parts.append(TextPart(content=current_text))

    return parts


async def send_message(user_input: str) -> None:
    """エージェントにメッセージを送信して応答を表示する。"""
    from src.core.models.agent_model import TextPart

    _display_user_message(user_input)

    with st.chat_message("assistant"):
        try:
            st.session_state.is_processing = True

            # ストリーミング開始前に待機インジケータを表示
            with st.spinner("エージェントが考え中..."):
                parts = await _stream_assistant_response(user_input)

            assistant_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                timestamp=datetime.now(),
                parts=parts,
            )
            st.session_state.chat_messages.append(assistant_message)

        except Exception as e:
            logger.error(f"メッセージ送信中にエラーが発生しました: {e}")
            error_msg = f"エラーが発生しました: {str(e)}"
            st.markdown(error_msg)
            st.session_state.chat_messages.append(
                ChatMessage(
                    role=MessageRole.ASSISTANT,
                    timestamp=datetime.now(),
                    parts=[TextPart(content=error_msg)],
                )
            )

        finally:
            st.session_state.is_processing = False


def handle_chat_controls(controls: dict) -> None:
    """チャットコントロールボタンのアクションを処理する。"""
    if controls["new_session"]:
        start_new_session()
        st.rerun()

    if controls["export_chat"]:
        export_conversation()


def export_conversation() -> None:
    """現在の会話をエクスポートする。"""
    if st.session_state.chat_messages:
        export_data = {
            "session_id": st.session_state.current_session_id,
            "exported_at": datetime.now().isoformat(),
            "messages": [msg.model_dump(mode="json") for msg in st.session_state.chat_messages],
        }
        st.download_button(
            label="📥 JSONをダウンロード",
            data=json.dumps(export_data, ensure_ascii=False, indent=2),
            file_name=f"chat_export_{st.session_state.current_session_id}.json",
            mime="application/json",
        )
    else:
        st.info("エクスポートする会話がありません")


def render_agent_chat_page(controls: dict) -> None:
    """エージェントチャットページをレンダリングする。"""
    logger.debug("エージェントチャットページをレンダリング中")

    # 選択されたモデルを取得
    selected_model = controls.get("selected_model", "claude-sonnet-4-20250514")

    # APIキーのチェック
    from src.infrastructure.llm.llm_factory import MODEL_CONFIGS

    model_config = MODEL_CONFIGS.get(selected_model)
    if not model_config:
        render_error_message(f"サポートされていないモデル: {selected_model}")
        st.stop()

    provider: str = model_config["provider"]  # type: ignore
    if provider == "anthropic" and not settings.anthropic_api_key:
        render_error_message(
            "Anthropic APIキーが設定されていません。.envファイルにANTHROPIC_API_KEYを設定してください。"
        )
        st.stop()
    elif provider == "openai" and not settings.openai_api_key:
        render_error_message("OpenAI APIキーが設定されていません。.envファイルにOPENAI_API_KEYを設定してください。")
        st.stop()

    initialize_session_state(selected_model)

    handle_chat_controls(controls)

    if st.session_state.chat_messages:
        render_chat_history(st.session_state.chat_messages)

    if user_input := render_chat_input():
        if not st.session_state.is_processing:
            asyncio.run(send_message(user_input))
            st.rerun()
        else:
            st.warning("メッセージを処理中です。しばらくお待ちください。")
