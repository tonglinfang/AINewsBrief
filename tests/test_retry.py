"""Tests for retry utilities."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from src.utils.retry import (
    async_retry,
    create_retry_config,
    CircuitBreaker,
    CircuitBreakerOpen,
)


class TestAsyncRetry:
    """Tests for async retry decorator."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_first_attempt(self):
        """Test that successful calls don't retry."""
        call_count = 0

        @async_retry(max_attempts=3)
        async def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_func()

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_failure(self):
        """Test that transient failures trigger retries."""
        call_count = 0

        @async_retry(max_attempts=3, min_wait=0.1, max_wait=0.2)
        async def failing_then_succeeding():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Transient failure")
            return "success"

        result = await failing_then_succeeding()

        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_max_attempts_exceeded(self):
        """Test that permanent failures exhaust retries."""
        call_count = 0

        @async_retry(max_attempts=3, min_wait=0.1, max_wait=0.2)
        async def always_failing():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Permanent failure")

        with pytest.raises(ConnectionError):
            await always_failing()

        assert call_count == 3


class TestCircuitBreaker:
    """Tests for circuit breaker."""

    @pytest.mark.asyncio
    async def test_circuit_stays_closed_on_success(self):
        """Test that successful calls keep circuit closed."""
        breaker = CircuitBreaker(failure_threshold=3, name="test")

        async def successful_call():
            return "success"

        result = await breaker.call(successful_call)

        assert result == "success"
        assert breaker.state == "closed"
        assert breaker.failures == 0

    @pytest.mark.asyncio
    async def test_circuit_opens_after_threshold(self):
        """Test that circuit opens after failure threshold."""
        breaker = CircuitBreaker(failure_threshold=3, name="test")

        async def failing_call():
            raise Exception("failure")

        # Trigger failures up to threshold
        for _ in range(3):
            with pytest.raises(Exception):
                await breaker.call(failing_call)

        assert breaker.state == "open"
        assert breaker.failures == 3

    @pytest.mark.asyncio
    async def test_circuit_rejects_when_open(self):
        """Test that open circuit rejects calls."""
        breaker = CircuitBreaker(
            failure_threshold=2, recovery_timeout=60, name="test"
        )

        async def failing_call():
            raise Exception("failure")

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(failing_call)

        # Next call should be rejected
        with pytest.raises(CircuitBreakerOpen):
            await breaker.call(failing_call)

    @pytest.mark.asyncio
    async def test_circuit_resets_on_success(self):
        """Test that circuit resets after successful call in half-open state."""
        breaker = CircuitBreaker(
            failure_threshold=2, recovery_timeout=0, name="test"
        )

        async def failing_call():
            raise Exception("failure")

        async def successful_call():
            return "success"

        # Open the circuit
        for _ in range(2):
            with pytest.raises(Exception):
                await breaker.call(failing_call)

        assert breaker.state == "open"

        # Allow immediate recovery (timeout=0)
        result = await breaker.call(successful_call)

        assert result == "success"
        assert breaker.state == "closed"
        assert breaker.failures == 0


class TestRetryConfig:
    """Tests for retry configuration."""

    def test_create_retry_config_defaults(self):
        """Test default retry configuration."""
        config = create_retry_config()

        assert config.stop.max_attempt_number == 3

    def test_create_retry_config_custom(self):
        """Test custom retry configuration."""
        config = create_retry_config(
            max_attempts=5,
            min_wait=2.0,
            max_wait=30.0,
        )

        assert config.stop.max_attempt_number == 5
