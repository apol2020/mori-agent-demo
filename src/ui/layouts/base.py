"""アプリケーションの基本レイアウト。"""

from typing import Literal, cast

import streamlit as st

from src.config.settings import settings


def setup_page_config() -> None:
    """基本的なページ設定をセットアップする。"""
    st.set_page_config(
        page_title=settings.page_title,
        page_icon=settings.page_icon,
        layout=cast(Literal["centered", "wide"], settings.layout),
        initial_sidebar_state=cast(
            Literal["auto", "expanded", "collapsed"],
            settings.initial_sidebar_state,
        ),
    )
