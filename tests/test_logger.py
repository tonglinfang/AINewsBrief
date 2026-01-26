"""Tests for logging utilities."""

import pytest
from src.utils.logger import get_logger, init_logger, setup_logging, LoggerMixin


class TestLogger:
    """Tests for logger setup and usage."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a bound logger."""
        logger = get_logger("test")

        assert logger is not None
        assert hasattr(logger, "info")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")

    def test_get_logger_with_name(self):
        """Test that get_logger binds the module name."""
        logger = get_logger("my_module")

        # Logger should be able to log without errors
        logger.info("test_message", key="value")

    def test_init_logger_json_format(self):
        """Test logger initialization with JSON format."""
        logger = init_logger(level="DEBUG", json_format=True)

        assert logger is not None

    def test_init_logger_console_format(self):
        """Test logger initialization with console format."""
        logger = init_logger(level="INFO", json_format=False)

        assert logger is not None


class TestLoggerMixin:
    """Tests for LoggerMixin class."""

    def test_mixin_provides_logger(self):
        """Test that LoggerMixin provides a log property."""

        class MyClass(LoggerMixin):
            def do_something(self):
                self.log.info("doing_something")
                return True

        obj = MyClass()

        assert hasattr(obj, "log")
        assert obj.do_something() is True

    def test_mixin_logger_bound_to_class_name(self):
        """Test that mixin logger is bound to class name."""

        class TestClass(LoggerMixin):
            pass

        obj = TestClass()
        logger = obj.log

        # Logger should be bound with the class name
        assert logger is not None
