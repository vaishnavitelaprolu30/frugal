"""
Chained High-Precision Micro-Interaction Dispatcher (Q1 Framework)

What it does:
    Dispatches a rapid action sequence (hover -> drag +15px on X axis -> click) on target
    canvas coordinates within a strict 30-100ms window following a pixel state transition.
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
    final_x: int
    final_y: int
    delta_x: int
    delta_y: int
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
        initial_x, initial_y = coords
        drag_distance = 15
        final_x = initial_x + drag_distance
        final_y = initial_y

        delta_x = final_x - initial_x
        delta_y = final_y - initial_y

        assert delta_x == 15, f"Expected delta_x == 15, got {delta_x}"
        assert delta_y == 0, f"Expected delta_y == 0, got {delta_y}"

        # Step 1: Mouse Hover
        page.mouse.move(initial_x, initial_y)

        # Step 2: Drag +15px on X axis
        page.mouse.down()
        page.mouse.move(final_x, final_y, steps=3)
        page.mouse.up()

        # Step 3: Click
        page.mouse.click(final_x, final_y)

        completion_ns = time.perf_counter_ns()
        latency_ms = (completion_ns - detection_ts_ns) / 1e6
        window_hit = (self.min_window_ms <= latency_ms <= self.max_window_ms)

        print(f"[ACTION CHAIN] initial_x={initial_x} initial_y={initial_y} final_x={final_x} final_y={final_y} delta_x={delta_x} delta_y={delta_y} latency_ms={latency_ms:.2f}ms")

        result = ActionLatencyResult(
            target_x=initial_x,
            target_y=initial_y,
            final_x=final_x,
            final_y=final_y,
            delta_x=delta_x,
            delta_y=delta_y,
            detection_ts_ns=detection_ts_ns,
            completion_ts_ns=completion_ns,
            latency_ms=latency_ms,
            window_hit=window_hit
        )

        logger.info(json.dumps({
            "event": "CHAINED_ACTION_DISPATCHED",
            "initial": [initial_x, initial_y],
            "final": [final_x, final_y],
            "delta_x": delta_x,
            "delta_y": delta_y,
            "latency_ms": round(latency_ms, 3),
            "window_hit": window_hit,
            "timestamp_micros": int(time.time() * 1e6)
        }))

        if not window_hit:
            raise RaceWindowMissedError(
                f"Action latency of {latency_ms:.2f}ms fell outside required {self.min_window_ms}-{self.max_window_ms}ms window."
            )

        return result
