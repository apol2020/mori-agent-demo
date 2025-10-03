"""LLM統合用のAnthropicクライアント。"""

# mypy: ignore-errors

from typing import Optional

from langchain_anthropic import ChatAnthropic

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


class AnthropicClient:
    """Anthropic API統合用のクライアント。"""

    def __init__(self, api_key: Optional[str] = None) -> None:
        """Anthropicクライアントを初期化する。"""
        self._api_key = api_key or settings.anthropic_api_key
        if not self._api_key:
            logger.warning("No Anthropic API key provided")

    def get_llm(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        streaming: bool = True,
    ) -> ChatAnthropic:
        """設定済みのAnthropic LLMインスタンスを取得する。"""
        model = model or settings.anthropic_model
        temperature = temperature if temperature is not None else settings.anthropic_temperature
        max_tokens = max_tokens or settings.anthropic_max_tokens

        logger.info(f"Creating Anthropic LLM with model: {model}")
        logger.debug(f"LLM config - temperature: {temperature}, max_tokens: {max_tokens}, streaming: {streaming}")

        try:
            llm = ChatAnthropic(  # type: ignore
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
                anthropic_api_key=self._api_key,
            )
            logger.debug("Anthropic LLM created successfully")
            return llm
        except Exception as e:
            logger.error(f"Failed to create Anthropic LLM: {e}")
            raise
