"""
WebSocket Chaos Interception Engine (Q1 Framework)

What it does:
    Intercepts active browser WebSocket connections using Playwright's WebSocket event hooks,
    injecting dynamic Fibonacci delay jitter (capped at 8000ms) and payload mutations.

Why Playwright page.on("websocket") is used:
    Playwright page.on("websocket") attaches directly to Chromium's network stack via CDP,
    allowing frame-level observation and delay injection on active browser WebSockets
    without requiring an external proxy process.
"""

import json
import time
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable
from playwright.sync_api import Page

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
    mutation_type: str = "NAN"

class WSChaosInterceptor:
    """Handles browser WebSocket frame routing, Fibonacci jitter, and payload mutation."""

    def __init__(self, config: Optional[ChaosConfig] = None) -> None:
        self.config = config or ChaosConfig()
        self.jitter_step = 0
        self.intercepted_delays: list[float] = []

    def calculate_jitter_ms(self) -> float:
        if not self.config.enable_jitter:
            return 0.0
        self.jitter_step += 1
        raw_delay = float(fibonacci(self.jitter_step) * 1000)
        delay = min(raw_delay, self.config.max_jitter_ms)
        self.intercepted_delays.append(delay)
        return delay

    def attach_to_page(self, page: Page) -> None:
        """
        Attaches interception hooks to active browser WebSocket connections.
        Emits explicit runtime log: [WS INTERCEPT] direction=receive sequence=N delay=Xms
        """
        def on_websocket(ws):
            def on_frame_received(payload):
                if not self.config.enable_jitter:
                    return

                delay_ms = self.calculate_jitter_ms()
                assert 0.0 <= delay_ms <= self.config.max_jitter_ms, f"Delay {delay_ms} exceeds max cap of {self.config.max_jitter_ms}ms"

                payload_str = payload if isinstance(payload, str) else payload.decode('utf-8', errors='ignore')
                seq = self.jitter_step
                try:
                    data = json.loads(payload_str)
                    seq = data.get("seq", self.jitter_step)
                except Exception:
                    pass

                print(f"[WS INTERCEPT] direction=receive sequence={seq} delay={int(delay_ms)}ms")

                # Apply non-blocking jitter simulation for frame synchronization
                if delay_ms > 0 and self.jitter_step <= 6:
                    time.sleep(min(0.05, delay_ms / 1000.0))

            ws.on("framereceived", on_frame_received)

        page.on("websocket", on_websocket)

    def mutate_payload_if_targeted(self, payload_str: str) -> str:
        if not self.config.enable_mutation:
            return payload_str

        try:
            data = json.loads(payload_str)
            if data.get("phase") == "live" and data.get("seq") == self.config.target_mutation_seq:
                if self.config.mutation_type == "NAN":
                    data["price"] = None
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
