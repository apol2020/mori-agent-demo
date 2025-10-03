"""アプリケーションのロガー設定モジュール。"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str,
    level: str = "INFO",
    format_str: Optional[str] = None,
) -> logging.Logger:
    """ロガーインスタンスを設定して構成する。

    Args:
        name: ロガー名（通常はモジュールの__name__）
        level: ロギングレベル（DEBUG、INFO、WARNING、ERROR、CRITICAL）
        format_str: オプションのカスタムフォーマット文字列

    Returns:
        設定済みのロガーインスタンス
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    if format_str is None:
        format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(format_str)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    logger.addHandler(console_handler)

    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """設定からデフォルト構成でロガーインスタンスを取得する。

    Args:
        name: ロガー名（通常はモジュールの__name__）

    Returns:
        設定済みのロガーインスタンス
    """
    from src.config.settings import settings

    return setup_logger(
        name=name,
        level=settings.log_level,
        format_str=settings.log_format,
    )
