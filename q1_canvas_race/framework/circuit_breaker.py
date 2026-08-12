"""
Circuit Breaker & Resilience Engine (Q1 Framework)

What it does:
    Monitors automation execution for failures (StaleFrameError, CoordinateDriftError, RepaintLagError)
    and manages state transitions (CLOSED -> OPEN -> HALF_OPEN) with automatic recalibration.

Failure mode defended against:
    Prevents cascading test failures and infinite retry loops caused by rendering lag
    or canvas layout offset changes.

Design trade-off:
    Chooses proactive cool-down periods and coordinate re-calibration over naive immediate
    retries, sacrificing execution speed in degraded states for long-term suite stability.
"""

import json
import time
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Callable, Any, Optional

logger = logging.getLogger("circuit_breaker")

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class StaleFrameError(Exception):
    """Raised when frame timestamps cease advancing."""
    pass

class CoordinateDriftError(Exception):
    """Raised when pixel sampling returns unexpected color distributions indicating offset drift."""
    pass

class RepaintLagError(Exception):
    """Raised when requestAnimationFrame loop drops below execution threshold."""
    pass

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 3
    cool_down_seconds: float = 2.0
    recalibrate_on_drift: bool = True

class CircuitBreaker:
    """Resilience wrapper enforcing circuit breaker policy and offset recalibration."""

    def __init__(self, config: Optional[CircuitBreakerConfig] = None) -> None:
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float = 0.0

    def transition_to(self, new_state: CircuitState) -> None:
        old_state = self.state
        self.state = new_state
        logger.info(json.dumps({
            "event": "CIRCUIT_BREAKER_TRANSITION",
            "from": old_state.value,
            "to": new_state.value,
            "failure_count": self.failure_count,
            "timestamp_micros": int(time.time() * 1e6)
        }))

    def execute(self, action: Callable[[], Any], recalibrate_fn: Optional[Callable[[], Any]] = None) -> Any:
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time > self.config.cool_down_seconds:
                self.transition_to(CircuitState.HALF_OPEN)
            else:
                raise RuntimeError(f"Circuit Breaker is OPEN. Cooling down (remaining: {self.config.cool_down_seconds - (now - self.last_failure_time):.2f}s)")

        try:
            result = action()
            if self.state == CircuitState.HALF_OPEN:
                self.failure_count = 0
                self.transition_to(CircuitState.CLOSED)
            return result
        except (StaleFrameError, CoordinateDriftError, RepaintLagError) as err:
            self.failure_count += 1
            self.last_failure_time = time.time()
            logger.warning(json.dumps({
                "event": "CIRCUIT_BREAKER_FAILURE_CAPTURED",
                "error_type": type(err).__name__,
                "error_msg": str(err),
                "failure_count": self.failure_count,
                "timestamp_micros": int(time.time() * 1e6)
            }))

            if isinstance(err, CoordinateDriftError) and self.config.recalibrate_on_drift and recalibrate_fn:
                logger.info("Triggering offset recalibration pass following CoordinateDriftError")
                recalibrate_fn()

            if self.failure_count >= self.config.failure_threshold:
                self.transition_to(CircuitState.OPEN)

            raise err
