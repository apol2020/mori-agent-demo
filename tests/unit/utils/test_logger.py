"""ロガー設定モジュールのユニットテスト"""

import logging
from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from src.utils.logger import get_logger, setup_logger


class TestSetupLogger:
    """setup_logger関数のテストスイート"""

    def test_setup_logger_with_default_params(self) -> None:
        """デフォルトパラメータでのロガー設定をテスト"""
        logger = setup_logger("test_logger")

        assert logger.name == "test_logger"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)

    def test_setup_logger_with_custom_level(self) -> None:
        """カスタムログレベルでのロガー設定をテスト"""
        logger = setup_logger("test_logger_debug", level="DEBUG")

        assert logger.level == logging.DEBUG
        assert logger.handlers[0].level == logging.DEBUG

    def test_setup_logger_with_custom_format(self) -> None:
        """カスタムフォーマット文字列でのロガー設定をテスト"""
        custom_format = "%(levelname)s - %(message)s"
        logger = setup_logger("test_logger_format", format_str=custom_format)

        formatter = logger.handlers[0].formatter
        assert formatter is not None
        assert formatter._fmt == custom_format

    def test_setup_logger_handles_invalid_level(self) -> None:
        """無効なログレベルでのロガー設定がINFOにデフォルト設定されることをテスト"""
        logger = setup_logger("test_logger_invalid", level="INVALID")

        assert logger.level == logging.INFO

    def test_setup_logger_no_duplicate_handlers(self) -> None:
        """setup_loggerを2回呼び出しても重複ハンドラーが作成されないことをテスト"""
        logger1 = setup_logger("test_logger_duplicate")
        initial_handler_count = len(logger1.handlers)

        logger2 = setup_logger("test_logger_duplicate")
        assert logger1 is logger2
        assert len(logger2.handlers) == initial_handler_count

    def test_logger_output_to_stdout(self) -> None:
        """ロガーが標準出力に出力することをテスト"""
        test_message = "Test log message"

        with patch("sys.stdout", new=StringIO()) as fake_stdout:
            logger = setup_logger("test_stdout_logger", level="INFO")
            logger.info(test_message)

            output = fake_stdout.getvalue()
            assert test_message in output

    def test_logger_no_propagation(self) -> None:
        """ロガーの伝播が無効化されていることをテスト"""
        logger = setup_logger("test_no_propagate")
        assert logger.propagate is False


class TestGetLogger:
    """get_logger関数のテストスイート"""

    @patch("src.config.settings.settings")
    def test_get_logger_uses_settings(self, mock_settings: MagicMock) -> None:
        """get_loggerが設定を使用して構成されることをテスト"""
        mock_settings.log_level = "WARNING"
        mock_settings.log_format = "%(message)s"

        with patch("src.utils.logger.setup_logger") as mock_setup:
            logger_name = "test_get_logger"
            get_logger(logger_name)

            mock_setup.assert_called_once_with(
                name=logger_name,
                level="WARNING",
                format_str="%(message)s",
            )

    @patch("src.config.settings.settings")
    def test_get_logger_returns_logger_instance(self, mock_settings: MagicMock) -> None:
        """get_loggerが有効なロガーインスタンスを返すことをテスト"""
        mock_settings.log_level = "INFO"
        mock_settings.log_format = "%(message)s"

        logger = get_logger("test_instance")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_instance"


class TestLoggerIntegration:
    """ロガー機能の統合テスト"""

    def test_logger_different_levels(self) -> None:
        """ロガーがレベルに応じてメッセージを正しくフィルタリングすることをテスト"""
        with patch("sys.stdout", new=StringIO()) as fake_stdout:
            logger = setup_logger("test_levels", level="WARNING")

            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

            output = fake_stdout.getvalue()

            assert "Debug message" not in output
            assert "Info message" not in output
            assert "Warning message" in output
            assert "Error message" in output

    def test_logger_format_includes_components(self) -> None:
        """デフォルトフォーマットに期待されるすべてのコンポーネントが含まれることをテスト"""
        with patch("sys.stdout", new=StringIO()) as fake_stdout:
            logger = setup_logger(
                "test_format_components",
                level="INFO",
                format_str="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )

            logger.info("Test message")
            output = fake_stdout.getvalue()

            assert "test_format_components" in output
            assert "INFO" in output
            assert "Test message" in output

    def test_multiple_loggers_independent(self) -> None:
        """複数のロガーが独立していることをテスト"""
        logger1 = setup_logger("logger1", level="DEBUG")
        logger2 = setup_logger("logger2", level="ERROR")

        assert logger1.level == logging.DEBUG
        assert logger2.level == logging.ERROR
        assert logger1 is not logger2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
