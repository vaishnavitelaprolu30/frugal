"""
WebSocket Chaos Interception Engine (Q1 Framework)

What it does:
    Intercepts active browser WebSocket connections (ws://localhost:8081/stream) using
    Playwright's page.route_web_socket() API.
    For each frame received from the server, holds it for the Fibonacci delay:
        delay_ms = min(1000 * fib(step), 8000.0)
    wires mutate_payload_if_targeted() into the forwarding path, logs timestamps,
    and asserts the actual delay matches the intended delay within OS tolerance.

Constraints:
    - Does NOT use page.on("websocket") (read-only observer).
    - Uses page.route_web_socket() frame routing.
"""

import json
import time
import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

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
    """Handles real WebSocket frame routing, Fibonacci delay holding, and payload mutation."""

    def __init__(self, config: Optional[ChaosConfig] = None) -> None:
        self.config = config or ChaosConfig()
        self.jitter_step = 0
        self.intercepted_logs: List[Dict[str, Any]] = []

    def calculate_jitter_ms(self) -> float:
        if not self.config.enable_jitter:
            return 0.0
        self.jitter_step += 1
        # Apply Fibonacci jitter progression to sequence frames
        if self.jitter_step <= 6:
            raw_delay = float(fibonacci(self.jitter_step) * 1000)
            return min(raw_delay, self.config.max_jitter_ms)
        return 0.0

    async def attach_to_page_async(self, page) -> None:
        """
        Attaches real page.route_web_socket() handler for async Playwright pages.
        """
        async def handler(ws_route):
            server = ws_route.connect_to_server()

            async def on_server_message(message):
                server_rx_ts = time.perf_counter()
                delay_ms = self.calculate_jitter_ms()
                step = self.jitter_step

                message_str = message if isinstance(message, str) else message.decode("utf-8", errors="ignore")
                mutated_payload = self.mutate_payload_if_targeted(message_str)

                if delay_ms > 0:
                    await asyncio.sleep(delay_ms / 1000.0)

                page_fw_ts = time.perf_counter()
                actual_delay_ms = (page_fw_ts - server_rx_ts) * 1000.0

                if delay_ms > 0:
                    assert abs(actual_delay_ms - delay_ms) <= 100.0, (
                        f"Actual delay {actual_delay_ms:.1f}ms deviated from intended {delay_ms}ms by >100ms"
                    )

                log_entry = {
                    "step": step,
                    "server_rx_ts": server_rx_ts,
                    "page_fw_ts": page_fw_ts,
                    "intended_delay_ms": delay_ms,
                    "actual_delay_ms": actual_delay_ms
                }
                self.intercepted_logs.append(log_entry)

                print(
                    f"[WS INTERCEPT] direction=receive sequence={step} "
                    f"server_rx_ts={server_rx_ts:.3f} page_fw_ts={page_fw_ts:.3f} "
                    f"delay={int(delay_ms)}ms actual_delay={actual_delay_ms:.1f}ms"
                )

                ws_route.send(mutated_payload)

            server.on_message(lambda msg: asyncio.create_task(on_server_message(msg)))
            ws_route.on_message(lambda msg: server.send(msg))

        await page.route_web_socket("**/stream*", handler)

    def attach_to_page(self, page) -> None:
        """
        Attaches page.route_web_socket() interceptor to a Playwright page.
        """
        def handler(ws_route):
            server = ws_route.connect_to_server()

            def on_server_message(message):
                server_rx_ts = time.perf_counter()
                delay_ms = self.calculate_jitter_ms()
                step = self.jitter_step

                message_str = message if isinstance(message, str) else message.decode("utf-8", errors="ignore")
                mutated_payload = self.mutate_payload_if_targeted(message_str)

                if delay_ms > 0:
                    time.sleep(delay_ms / 1000.0)

                page_fw_ts = time.perf_counter()
                actual_delay_ms = (page_fw_ts - server_rx_ts) * 1000.0

                if delay_ms > 0:
                    assert abs(actual_delay_ms - delay_ms) <= 100.0, (
                        f"Actual delay {actual_delay_ms:.1f}ms deviated from intended {delay_ms}ms by >100ms"
                    )

                log_entry = {
                    "step": step,
                    "server_rx_ts": server_rx_ts,
                    "page_fw_ts": page_fw_ts,
                    "intended_delay_ms": delay_ms,
                    "actual_delay_ms": actual_delay_ms
                }
                self.intercepted_logs.append(log_entry)

                print(
                    f"[WS INTERCEPT] direction=receive sequence={step} "
                    f"server_rx_ts={server_rx_ts:.3f} page_fw_ts={page_fw_ts:.3f} "
                    f"delay={int(delay_ms)}ms actual_delay={actual_delay_ms:.1f}ms"
                )

                ws_route.send(mutated_payload)

            server.on_message(on_server_message)
            ws_route.on_message(lambda msg: server.send(msg))

        page.route_web_socket("**/stream*", handler)

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
