"""LLMインスタンスを生成するファクトリー。"""

# mypy: ignore-errors

from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)


# モデル設定の定義（ハードコーディング）
MODEL_CONFIGS = {
    "claude-sonnet-4-20250514": {
        "provider": "anthropic",
        "model_name": "claude-sonnet-4-20250514",
    },
    "gpt-5": {
        "provider": "openai",
        "model_name": "gpt-5",
    },
    "gpt-5-mini": {
        "provider": "openai",
        "model_name": "gpt-5-mini",
    },
}


def create_llm(model_id: str, streaming: bool = True) -> Any:
    """指定されたモデルIDに基づいてLLMインスタンスを作成する。

    Args:
        model_id: モデルID（例: "claude-sonnet-4-20250514", "gpt-5", "gpt-5-mini"）
        streaming: ストリーミングを有効にするかどうか

    Returns:
        LLMインスタンス（ChatAnthropic または ChatOpenAI）

    Raises:
        ValueError: サポートされていないモデルIDの場合
        RuntimeError: 必要なAPIキーが設定されていない場合
    """
    if model_id not in MODEL_CONFIGS:
        raise ValueError(f"Unsupported model: {model_id}. Supported models: {list(MODEL_CONFIGS.keys())}")

    config = MODEL_CONFIGS[model_id]
    provider = config["provider"]
    model_name = config["model_name"]

    logger.info(f"Creating LLM: provider={provider}, model={model_name}")

    if provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")

        return ChatAnthropic(  # type: ignore
            model=model_name,
            streaming=streaming,
            anthropic_api_key=settings.anthropic_api_key,
        )

    elif provider == "openai":
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")

        return ChatOpenAI(  # type: ignore
            model=model_name,
            streaming=streaming,
            openai_api_key=settings.openai_api_key,
        )

    else:
        raise ValueError(f"Unsupported provider: {provider}")


def get_available_models() -> list[dict[str, str]]:
    """利用可能なモデルのリストを取得する。

    Returns:
        モデル情報の辞書のリスト（id, nameを含む）
    """
    models = []
    for model_id, config in MODEL_CONFIGS.items():
        provider = config["provider"]
        model_name = config["model_name"]
        # 表示用の名前を作成
        if provider == "anthropic":
            display_name = "Claude Sonnet 4.5"
        elif provider == "openai":
            if "mini" in model_name:
                display_name = "GPT-5 mini"
            else:
                display_name = "GPT-5"
        else:
            display_name = model_name

        models.append({"id": model_id, "name": display_name})

    return models
