"""Structured logging configuration using structlog."""

import logging
import sys
from typing import Optional

import structlog
from structlog.types import Processor


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[str] = None,
) -> structlog.BoundLogger:
    """Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_format: If True, output JSON format (for production)
        log_file: Optional file path to write logs

    Returns:
        Configured logger instance
    """
    # Shared processors for all outputs
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        # Production: JSON output
        processors: list[Processor] = [
            *shared_processors,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Colored console output
        processors = [
            *shared_processors,
            structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging to use structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper(), logging.INFO),
    )

    # Optionally add file handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        logging.getLogger().addHandler(file_handler)

    return structlog.get_logger()


# Global logger instance
_logger: Optional[structlog.BoundLogger] = None


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a logger instance with optional name binding.

    Args:
        name: Optional logger name (typically module name)

    Returns:
        Bound logger instance
    """
    global _logger
    if _logger is None:
        _logger = setup_logging()

    if name:
        return _logger.bind(module=name)
    return _logger


def init_logger(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[str] = None,
) -> structlog.BoundLogger:
    """Initialize the global logger with custom settings.

    Args:
        level: Log level
        json_format: Use JSON format for production
        log_file: Optional log file path

    Returns:
        Configured logger instance
    """
    global _logger
    _logger = setup_logging(level, json_format, log_file)
    return _logger


class LoggerMixin:
    """Mixin class to add logging capability to any class."""

    @property
    def log(self) -> structlog.BoundLogger:
        """Get logger bound with class name."""
        return get_logger(self.__class__.__name__)
