"""メインStreamlitアプリケーションのエントリーポイント。"""

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

from src.ui.components.sidebar import render_sidebar
from src.ui.layouts.base import setup_page_config
from src.ui.pages.agent_chat import render_agent_chat_page
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main() -> None:
    """メインアプリケーションのエントリーポイント。"""
    logger.info("Starting Streamlit application")

    # ページ設定をセットアップ
    setup_page_config()
    logger.debug("Page configuration completed")

    # ユーザー設定読み込み
    yaml_path = "login_cofig/config.yaml"

    with open(yaml_path) as file:
        config = yaml.load(file, Loader=SafeLoader)

    authenticator = stauth.Authenticate(
        credentials=config["credentials"],
        cookie_name=config["cookie"]["name"],
        cookie_key=config["cookie"]["key"],
        cookie_expiry_days=config["cookie"]["expiry_days"],
    )

    # UI - ログイン処理
    authenticator.login()

    if st.session_state["authentication_status"]:
        # ログイン成功 - ユーザー名をセッションに明示的に保存
        # streamlit-authenticatorは"username"キーにユーザー名を保存するが、
        # ログアウト→ログインでユーザーが切り替わった際に確実に更新されるよう明示的に設定
        if "username" in st.session_state:
            # ログイン中のユーザー名を記録
            current_username = st.session_state["username"]

            # 前回のユーザーと異なる場合、会話履歴をクリア（プライバシー保護）
            if "last_authenticated_user" in st.session_state:
                if st.session_state["last_authenticated_user"] != current_username:
                    logger.info(
                        f"User changed from {st.session_state['last_authenticated_user']} to {current_username}"
                    )
                    # 会話関連のセッションデータをクリア
                    for key in ["chat_messages", "current_session_id", "agent_service", "previous_username"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    logger.info("Cleared chat session data for user switch")

            # 現在のユーザー名を記録
            st.session_state["last_authenticated_user"] = current_username
            logger.info(f"Current logged-in user: {current_username}")

        with st.sidebar:
            st.markdown(f'## Welcome *{st.session_state["name"]}*')
            authenticator.logout("Logout", "sidebar")
            st.divider()

        # サイドバーをレンダリングしてチャットコントロールを取得
        controls = render_sidebar()

        # コントロールと共にエージェントチャットページをレンダリング
        render_agent_chat_page(controls)

    elif st.session_state["authentication_status"] is False:
        # ログイン失敗
        st.error("Username/password is incorrect")

    elif st.session_state["authentication_status"] is None:
        # ログアウト状態またはデフォルト
        # 会話関連のセッションデータをクリア（ログアウト時）
        if "last_authenticated_user" in st.session_state:
            logger.info(f"User {st.session_state['last_authenticated_user']} logged out, clearing session data")
            for key in [
                "chat_messages",
                "current_session_id",
                "agent_service",
                "previous_username",
                "last_authenticated_user",
            ]:
                if key in st.session_state:
                    del st.session_state[key]

        st.warning("Please enter your username and password")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Application crashed: {e}")
        raise
