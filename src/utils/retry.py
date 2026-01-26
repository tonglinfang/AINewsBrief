"""Retry utilities with exponential backoff."""

import asyncio
from functools import wraps
from typing import Any, Callable, Optional, Tuple, Type, TypeVar

import aiohttp
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from src.utils.logger import get_logger

T = TypeVar("T")

# Common retryable exceptions
RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    aiohttp.ClientError,
    aiohttp.ServerTimeoutError,
    asyncio.TimeoutError,
    ConnectionError,
    TimeoutError,
)

logger = get_logger("retry")


def create_retry_config(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
) -> AsyncRetrying:
    """Create a tenacity retry configuration.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        retryable_exceptions: Tuple of exception types to retry on

    Returns:
        Configured AsyncRetrying instance
    """
    exceptions = retryable_exceptions or RETRYABLE_EXCEPTIONS

    return AsyncRetrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        retry=retry_if_exception_type(exceptions),
        reraise=True,
    )


def async_retry(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
) -> Callable:
    """Decorator for async functions with retry logic.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries
        max_wait: Maximum wait time between retries
        retryable_exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic
    """
    exceptions = retryable_exceptions or RETRYABLE_EXCEPTIONS

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            retry_config = create_retry_config(
                max_attempts=max_attempts,
                min_wait=min_wait,
                max_wait=max_wait,
                retryable_exceptions=exceptions,
            )

            attempt = 0
            async for attempt_ctx in retry_config:
                with attempt_ctx:
                    attempt += 1
                    if attempt > 1:
                        logger.warning(
                            "retrying_request",
                            function=func.__name__,
                            attempt=attempt,
                            max_attempts=max_attempts,
                        )
                    return await func(*args, **kwargs)

            # This should never be reached due to reraise=True
            raise RuntimeError("Retry logic failed unexpectedly")

        return wrapper

    return decorator


async def fetch_with_retry(
    session: aiohttp.ClientSession,
    url: str,
    method: str = "GET",
    max_attempts: int = 3,
    timeout: float = 30.0,
    **kwargs: Any,
) -> aiohttp.ClientResponse:
    """Fetch URL with automatic retry on transient failures.

    Args:
        session: aiohttp ClientSession
        url: URL to fetch
        method: HTTP method
        max_attempts: Maximum retry attempts
        timeout: Request timeout in seconds
        **kwargs: Additional arguments passed to session.request

    Returns:
        aiohttp ClientResponse

    Raises:
        aiohttp.ClientError: If all retries fail
    """
    retry_config = create_retry_config(max_attempts=max_attempts)
    timeout_config = aiohttp.ClientTimeout(total=timeout)

    async for attempt in retry_config:
        with attempt:
            async with session.request(
                method, url, timeout=timeout_config, **kwargs
            ) as response:
                # Raise for server errors (5xx) to trigger retry
                if response.status >= 500:
                    raise aiohttp.ClientResponseError(
                        response.request_info,
                        response.history,
                        status=response.status,
                        message=f"Server error: {response.status}",
                    )
                return response

    raise aiohttp.ClientError(f"Failed to fetch {url} after {max_attempts} attempts")


class CircuitBreaker:
    """Simple circuit breaker implementation for protecting external services."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        name: str = "default",
    ):
        """Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name
        self.failures = 0
        self.last_failure_time: Optional[float] = None
        self.state = "closed"  # closed, open, half-open
        self._logger = get_logger(f"circuit_breaker.{name}")

    async def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerOpen: If circuit is open
            Exception: If function raises and circuit trips
        """
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
                self._logger.info("circuit_half_open", name=self.name)
            else:
                raise CircuitBreakerOpen(f"Circuit breaker {self.name} is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        import time

        return (time.time() - self.last_failure_time) >= self.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful call."""
        if self.state == "half-open":
            self._logger.info("circuit_closed", name=self.name)
        self.failures = 0
        self.state = "closed"

    def _on_failure(self) -> None:
        """Handle failed call."""
        import time

        self.failures += 1
        self.last_failure_time = time.time()

        if self.failures >= self.failure_threshold:
            self.state = "open"
            self._logger.warning(
                "circuit_opened",
                name=self.name,
                failures=self.failures,
                threshold=self.failure_threshold,
            )


class CircuitBreakerOpen(Exception):
    """Raised when circuit breaker is open."""

    pass
