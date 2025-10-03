"""アプリケーションのサイドバーコンポーネント。"""

import streamlit as st

from src.config.settings import settings
from src.core.tools import tool_registry
from src.infrastructure.llm.llm_factory import get_available_models


def render_sidebar() -> dict:
    """サイドバーをレンダリングしてチャットコントロールの状態を返す。"""
    with st.sidebar:
        st.title(settings.app_name)
        st.markdown("---")

        # モデル選択
        st.markdown("### 🤖 モデル選択")
        available_models = get_available_models()
        model_names = [model["name"] for model in available_models]
        model_ids = [model["id"] for model in available_models]

        # デフォルト選択（Claude Sonnet 4.5）
        default_index = 0

        selected_index = st.selectbox(
            "使用するモデル",
            range(len(model_names)),
            format_func=lambda i: model_names[i],
            index=default_index,
            label_visibility="collapsed",
        )

        selected_model_id = model_ids[selected_index]

        st.markdown("---")

        # チャットコントロール
        st.markdown("### 🎛️ コントロール")
        from src.ui.components.chat_interface import render_chat_controls

        controls = render_chat_controls(use_container_width=True)
        controls["selected_model"] = selected_model_id

        st.markdown("---")

        # 利用可能なツール（ツールレジストリから自動取得）
        st.markdown("### 🛠️ 利用可能なツール")
        tool_descriptions = tool_registry.get_tool_descriptions()
        if tool_descriptions:
            for idx, tool_info in enumerate(tool_descriptions, 1):
                st.markdown(f"{idx}. **{tool_info['name']}**: {tool_info['description']}")
        else:
            st.info("登録されているツールはありません")

        st.markdown("---")

        # デバッグモード情報
        if settings.debug:
            st.warning("Debug mode is enabled")
            st.caption(f"Version: {settings.app_version}")

    return controls
