"""
Chained High-Precision Micro-Interaction Dispatcher (Q1 Framework)

What it does:
    Dispatches a rapid action sequence (hover -> drag +15px on X axis -> click) on target
    canvas coordinates, measuring reaction latency to the START of the first mouse action.
"""

import time
import json
import logging
from dataclasses import dataclass
from typing import Tuple
from playwright.sync_api import Page

logger = logging.getLogger("chained_actions")

class RaceWindowMissedError(Exception):
    """Raised when action execution latency exceeds upper bound limit (100ms)."""
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
    start_action_ns: int
    completion_ts_ns: int
    latency_ms: float
    action_duration_ms: float
    window_hit: bool

class ChainedActionDispatcher:
    """Executes hover -> drag +15px -> click sequence with latency validation."""

    def __init__(self, min_window_ms: float = 0.0, max_window_ms: float = 100.0) -> None:
        self.min_window_ms = min_window_ms
        self.max_window_ms = max_window_ms

    def fire(self, page: Page, coords: Tuple[int, int], detection_ts_ns: int) -> ActionLatencyResult:
        initial_x, initial_y = coords
        drag_distance = 15
        final_x = initial_x + drag_distance
        final_y = initial_y

        delta_x = final_x - initial_x
        delta_y = final_y - initial_y

        start_action_ns = time.perf_counter_ns()
        latency_ms = (start_action_ns - detection_ts_ns) / 1e6

        # Step 1: Mouse Hover
        page.mouse.move(initial_x, initial_y)

        # Step 2: Drag +15px on X axis
        page.mouse.down()
        page.mouse.move(final_x, final_y, steps=3)
        page.mouse.up()

        # Step 3: Click
        page.mouse.click(final_x, final_y)

        completion_ns = time.perf_counter_ns()
        action_duration_ms = (completion_ns - start_action_ns) / 1e6

        window_hit = (latency_ms <= self.max_window_ms)

        if latency_ms < 30.0:
            print(f"[FAST RACE RESULT] latency_ms={latency_ms:.2f}ms < 30ms (PASS - rapid detection)")
        else:
            print(f"[ACTION CHAIN] initial_x={initial_x} initial_y={initial_y} final_x={final_x} final_y={final_y} delta_x={delta_x} delta_y={delta_y} latency_ms={latency_ms:.2f}ms duration_ms={action_duration_ms:.2f}ms")

        result = ActionLatencyResult(
            target_x=initial_x,
            target_y=initial_y,
            final_x=final_x,
            final_y=final_y,
            delta_x=delta_x,
            delta_y=delta_y,
            detection_ts_ns=detection_ts_ns,
            start_action_ns=start_action_ns,
            completion_ts_ns=completion_ns,
            latency_ms=latency_ms,
            action_duration_ms=action_duration_ms,
            window_hit=window_hit
        )

        logger.info(json.dumps({
            "event": "CHAINED_ACTION_DISPATCHED",
            "initial": [initial_x, initial_y],
            "final": [final_x, final_y],
            "delta_x": delta_x,
            "delta_y": delta_y,
            "latency_ms": round(latency_ms, 3),
            "action_duration_ms": round(action_duration_ms, 3),
            "window_hit": window_hit,
            "timestamp_micros": int(time.time() * 1e6)
        }))

        if not window_hit:
            raise RaceWindowMissedError(
                f"Action latency of {latency_ms:.2f}ms exceeded upper bound limit of {self.max_window_ms}ms."
            )

        return result
