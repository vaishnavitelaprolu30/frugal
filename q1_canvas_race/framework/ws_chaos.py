"""
WebSocket Chaos Interception Engine (Q1 Framework)

What it does:
    Intercepts WebSocket frames between Playwright client and server to inject
    Fibonacci delay jitter and mutate payload data on targeted sequence frames.

Failure mode defended against:
    Prevents test runner synchronization failures caused by sudden network degradation
    or malformed price payloads from causing uncaught silent failures or unhandled crashes.

Design trade-off:
    Uses Playwright WebSocket routing at the client level rather than a external proxy
    process, sacrificing raw network layer simulation for 100% deterministic test-process isolation.
"""

import json
import time
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger("ws_chaos")

def fibonacci(n: int) -> int:
    """Returns the n-th Fibonacci number."""
    if n <= 0:
        return 0
    if n == 1:
        return 1
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

@dataclass
class ChaosConfig:
    enable_jitter: bool = True
    enable_mutation: bool = True
    max_jitter_ms: float = 8000.0
    target_mutation_seq: int = 25
    mutation_type: str = "NAN"  # "NAN" | "OVERFLOW" | "FLOAT_ARTIFACT"

class WSChaosInterceptor:
    """Handles WebSocket frame routing, Fibonacci jitter, and payload mutation."""

    def __init__(self, config: Optional[ChaosConfig] = None) -> None:
        self.config = config or ChaosConfig()
        self.jitter_step = 0

    def calculate_jitter_ms(self) -> float:
        if not self.config.enable_jitter:
            return 0.0
        self.jitter_step += 1
        raw_delay = float(fibonacci(self.jitter_step) * 1000)
        return min(raw_delay, self.config.max_jitter_ms)

    def mutate_payload_if_targeted(self, payload_str: str) -> str:
        if not self.config.enable_mutation:
            return payload_str

        try:
            data = json.loads(payload_str)
            if data.get("phase") == "live" and data.get("seq") == self.config.target_mutation_seq:
                if self.config.mutation_type == "NAN":
                    data["price"] = None  # Will parse as null / non-finite in JS
                elif self.config.mutation_type == "OVERFLOW":
                    data["price"] = 1e+7
                elif self.config.mutation_type == "FLOAT_ARTIFACT":
                    data["price"] = 0.1 + 0.2
                
                logger.info(json.dumps({
                    "event": "PAYLOAD_MUTATED",
                    "seq": data.get("seq"),
                    "mutation_type": self.config.mutation_type,
                    "timestamp_micros": int(time.time() * 1e6)
                }))
                return json.dumps(data)
        except Exception as err:
            logger.warning(f"Error checking payload for mutation: {err}")

        return payload_str
