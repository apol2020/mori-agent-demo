"""メインStreamlitアプリケーションのエントリーポイント。"""

import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

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
        credentials=config['credentials'],
        cookie_name=config['cookie']['name'],
        cookie_key=config['cookie']['key'],
        cookie_expiry_days=config['cookie']['expiry_days'],
    )

    # UI - ログイン処理
    authenticator.login()

    if st.session_state["authentication_status"]:
        # ログイン成功
        with st.sidebar:
            st.markdown(f'## Welcome *{st.session_state["name"]}*')
            authenticator.logout('Logout', 'sidebar')
            st.divider()

        # サイドバーをレンダリングしてチャットコントロールを取得
        controls = render_sidebar()

        # コントロールと共にエージェントチャットページをレンダリング
        render_agent_chat_page(controls)

    elif st.session_state["authentication_status"] is False:
        # ログイン失敗
        st.error('Username/password is incorrect')

    elif st.session_state["authentication_status"] is None:
        # デフォルト
        st.warning('Please enter your username and password')


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Application crashed: {e}")
        raise
