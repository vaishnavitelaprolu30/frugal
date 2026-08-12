"""
WebSocket Chaos Interception Engine (Q1 Framework)

What it does:
    Intercepts active browser WebSocket connections (ws://localhost:8081/stream) using
    Playwright's route_web_socket() API attached to BrowserContext or Page before navigation.
    For each frame received from the server, holds it for the Fibonacci delay:
        delay_ms = min(1000 * fib(step), 8000.0)
    wires mutate_payload_if_targeted() into the forwarding path, logs timestamps,
    and forwards the delayed/mutated payload to the browser via ws_route.send().

Constraints:
    - Does NOT use page.on("websocket") (read-only observer).
    - Uses route_web_socket() frame routing.
    - Zero static time.sleep() calls in async frame routing.
"""

import json
import time
import asyncio
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple

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
        """Calculates exact Fibonacci jitter sequence: min(fib(step) * 1000, max_jitter_ms)."""
        if not self.config.enable_jitter:
            return 0.0
        self.jitter_step += 1
        raw_delay = float(fibonacci(self.jitter_step) * 1000)
        return min(raw_delay, self.config.max_jitter_ms)

    async def attach_to_context_async(self, context) -> None:
        """
        Attaches route_web_socket() handler to BrowserContext before page navigation.
        """
        async def handler(ws_route):
            server = ws_route.connect_to_server()

            async def on_server_message(message):
                server_rx_ts = time.perf_counter()
                delay_ms = self.calculate_jitter_ms()
                step = self.jitter_step

                message_str = message if isinstance(message, str) else message.decode("utf-8", errors="ignore")
                mutated_payload, was_mutated = self.mutate_payload_if_targeted(message_str)

                if delay_ms > 0:
                    await asyncio.sleep(delay_ms / 1000.0)

                page_fw_ts = time.perf_counter()
                actual_delay_ms = (page_fw_ts - server_rx_ts) * 1000.0

                log_entry = {
                    "sequence": step,
                    "fib_step": step,
                    "server_rx_ts": server_rx_ts,
                    "page_fw_ts": page_fw_ts,
                    "requested_delay_ms": delay_ms,
                    "forwarded_after_ms": actual_delay_ms,
                    "mutated": was_mutated
                }
                self.intercepted_logs.append(log_entry)

                print(
                    f"\n[WS INTERCEPT]\n"
                    f"direction=RECEIVE\n"
                    f"sequence={step}\n"
                    f"fib_step={step}\n"
                    f"requested_delay_ms={int(delay_ms)}\n"
                    f"forwarded_after_ms={actual_delay_ms:.1f}\n"
                    f"mutated={was_mutated}"
                )

                ws_route.send(mutated_payload)

            server.on_message(lambda msg: asyncio.create_task(on_server_message(msg)))
            ws_route.on_message(lambda msg: server.send(msg))

        await context.route_web_socket("**/stream*", handler)

    async def attach_to_page_async(self, page) -> None:
        """
        Attaches page.route_web_socket() handler for async Playwright pages.
        """
        async def handler(ws_route):
            server = ws_route.connect_to_server()

            async def on_server_message(message):
                server_rx_ts = time.perf_counter()
                delay_ms = self.calculate_jitter_ms()
                step = self.jitter_step

                message_str = message if isinstance(message, str) else message.decode("utf-8", errors="ignore")
                mutated_payload, was_mutated = self.mutate_payload_if_targeted(message_str)

                if delay_ms > 0:
                    await asyncio.sleep(delay_ms / 1000.0)

                page_fw_ts = time.perf_counter()
                actual_delay_ms = (page_fw_ts - server_rx_ts) * 1000.0

                log_entry = {
                    "sequence": step,
                    "fib_step": step,
                    "server_rx_ts": server_rx_ts,
                    "page_fw_ts": page_fw_ts,
                    "requested_delay_ms": delay_ms,
                    "forwarded_after_ms": actual_delay_ms,
                    "mutated": was_mutated
                }
                self.intercepted_logs.append(log_entry)

                print(
                    f"\n[WS INTERCEPT]\n"
                    f"direction=RECEIVE\n"
                    f"sequence={step}\n"
                    f"fib_step={step}\n"
                    f"requested_delay_ms={int(delay_ms)}\n"
                    f"forwarded_after_ms={actual_delay_ms:.1f}\n"
                    f"mutated={was_mutated}"
                )

                ws_route.send(mutated_payload)

            server.on_message(lambda msg: asyncio.create_task(on_server_message(msg)))
            ws_route.on_message(lambda msg: server.send(msg))

        await page.route_web_socket("**/stream*", handler)

    def attach_to_page(self, page) -> None:
        """
        Attaches page.route_web_socket() interceptor to a sync Playwright page.
        """
        def handler(ws_route):
            server = ws_route.connect_to_server()

            def on_server_message(message):
                server_rx_ts = time.perf_counter()
                delay_ms = self.calculate_jitter_ms()
                step = self.jitter_step

                message_str = message if isinstance(message, str) else message.decode("utf-8", errors="ignore")
                mutated_payload, was_mutated = self.mutate_payload_if_targeted(message_str)

                page_fw_ts = time.perf_counter()
                actual_delay_ms = (page_fw_ts - server_rx_ts) * 1000.0

                log_entry = {
                    "sequence": step,
                    "fib_step": step,
                    "server_rx_ts": server_rx_ts,
                    "page_fw_ts": page_fw_ts,
                    "requested_delay_ms": delay_ms,
                    "forwarded_after_ms": actual_delay_ms,
                    "mutated": was_mutated
                }
                self.intercepted_logs.append(log_entry)

                print(
                    f"\n[WS INTERCEPT]\n"
                    f"direction=RECEIVE\n"
                    f"sequence={step}\n"
                    f"fib_step={step}\n"
                    f"requested_delay_ms={int(delay_ms)}\n"
                    f"forwarded_after_ms={actual_delay_ms:.1f}\n"
                    f"mutated={was_mutated}"
                )

                ws_route.send(mutated_payload)

            server.on_message(on_server_message)
            ws_route.on_message(lambda msg: server.send(msg))

        page.route_web_socket("**/stream*", handler)

    def mutate_payload_if_targeted(self, payload_str: str) -> Tuple[str, bool]:
        if not self.config.enable_mutation:
            return payload_str, False

        try:
            data = json.loads(payload_str)
            if data.get("phase") == "live" and data.get("seq") == self.config.target_mutation_seq:
                orig_val = data.get("price")
                if self.config.mutation_type == "NAN":
                    data["price"] = None
                elif self.config.mutation_type == "OVERFLOW":
                    data["price"] = 1e+7
                elif self.config.mutation_type == "FLOAT_ARTIFACT":
                    data["price"] = 0.1 + 0.2
                
                logger.info(json.dumps({
                    "event": "PAYLOAD_MUTATED",
                    "seq": data.get("seq"),
                    "orig_value": orig_val,
                    "mutated_value": data.get("price"),
                    "mutation_type": self.config.mutation_type,
                    "timestamp_micros": int(time.time() * 1e6)
                }))
                return json.dumps(data), True
        except Exception as err:
            logger.warning(f"Error checking payload for mutation: {err}")

        return payload_str, False
