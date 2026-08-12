"""
Chained High-Precision Micro-Interaction Dispatcher (Q1 Framework)

What it does:
    Dispatches a rapid action sequence (hover -> drag +15px -> click) on target canvas coordinates
    within a strict 30-100ms window following a pixel state transition.

Failure mode defended against:
    Defends against race window misses where transient cell states flip before input events register.

Design trade-off:
    Uses synthesized Playwright CDP/Mouse events rather than native OS level events,
    trading raw OS input driver fidelity for microsecond-precise event timing control.
"""

import time
import json
import logging
from dataclasses import dataclass
from typing import Tuple
from playwright.sync_api import Page

logger = logging.getLogger("chained_actions")

class RaceWindowMissedError(Exception):
    """Raised when action execution latency falls outside the required 30-100ms window."""
    pass

@dataclass
class ActionLatencyResult:
    target_x: int
    target_y: int
    detection_ts_ns: int
    completion_ts_ns: int
    latency_ms: float
    window_hit: bool

class ChainedActionDispatcher:
    """Executes hover -> drag +15px -> click sequence with latency validation."""

    def __init__(self, min_window_ms: float = 30.0, max_window_ms: float = 100.0) -> None:
        self.min_window_ms = min_window_ms
        self.max_window_ms = max_window_ms

    def fire(self, page: Page, coords: Tuple[int, int], detection_ts_ns: int) -> ActionLatencyResult:
        cx, cy = coords
        start_ns = time.perf_counter_ns()

        # Step 1: Mouse Hover
        page.mouse.move(cx, cy)

        # Step 2: Drag +15px on X axis
        page.mouse.down()
        page.mouse.move(cx + 15, cy, steps=3)
        page.mouse.up()

        # Step 3: Click
        page.mouse.click(cx + 15, cy)

        completion_ns = time.perf_counter_ns()
        latency_ms = (completion_ns - detection_ts_ns) / 1e6
        window_hit = (self.min_window_ms <= latency_ms <= self.max_window_ms)

        result = ActionLatencyResult(
            target_x=cx,
            target_y=cy,
            detection_ts_ns=detection_ts_ns,
            completion_ts_ns=completion_ns,
            latency_ms=latency_ms,
            window_hit=window_hit
        )

        logger.info(json.dumps({
            "event": "CHAINED_ACTION_DISPATCHED",
            "coords": [cx, cy],
            "latency_ms": round(latency_ms, 3),
            "window_hit": window_hit,
            "timestamp_micros": int(time.time() * 1e6)
        }))

        if not window_hit:
            raise RaceWindowMissedError(
                f"Action latency of {latency_ms:.2f}ms fell outside required {self.min_window_ms}-{self.max_window_ms}ms window."
            )

        return result
