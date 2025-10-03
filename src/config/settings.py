"""アプリケーション設定と構成。"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """環境変数から読み込まれるアプリケーション設定。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # アプリケーション
    app_name: str = "Mori Agent Demo"
    app_version: str = "0.1.0"
    debug: bool = False

    # Streamlit
    page_title: str = "Mori Agent Demo"
    page_icon: str = "🤖"
    layout: str = "wide"  # Literal["centered", "wide"]
    initial_sidebar_state: str = "expanded"  # Literal["auto", "expanded", "collapsed"]

    # ロギング設定
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Anthropic設定
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-20250514"
    anthropic_temperature: float = 0.0
    anthropic_max_tokens: int = 4096

    # OpenAI設定
    openai_api_key: Optional[str] = None


# グローバル設定インスタンス
settings = AppSettings()
