"""メインStreamlitアプリケーションのエントリーポイント。"""

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

    # サイドバーをレンダリングしてチャットコントロールを取得
    controls = render_sidebar()

    # コントロールと共にエージェントチャットページをレンダリング
    render_agent_chat_page(controls)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Application crashed: {e}")
        raise
