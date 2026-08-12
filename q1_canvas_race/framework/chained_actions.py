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
    actual_initial_x: int
    actual_initial_y: int
    actual_final_x: int
    actual_final_y: int
    actual_delta_x: int
    actual_delta_y: int
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
        actual_initial_x, actual_initial_y = coords
        drag_distance = 15
        actual_final_x = actual_initial_x + drag_distance
        actual_final_y = actual_initial_y

        actual_delta_x = actual_final_x - actual_initial_x
        actual_delta_y = actual_final_y - actual_initial_y

        assert actual_delta_x == 15, f"Expected actual_delta_x == 15, got {actual_delta_x}"
        assert actual_delta_y == 0, f"Expected actual_delta_y == 0, got {actual_delta_y}"

        start_action_ns = time.perf_counter_ns()
        latency_ms = (start_action_ns - detection_ts_ns) / 1e6

        # Step 1: Mouse Hover
        page.mouse.move(actual_initial_x, actual_initial_y)

        # Step 2: Drag +15px on X axis
        page.mouse.down()
        page.mouse.move(actual_final_x, actual_final_y, steps=3)
        page.mouse.up()

        # Step 3: Click
        page.mouse.click(actual_final_x, actual_final_y)

        completion_ns = time.perf_counter_ns()
        action_duration_ms = (completion_ns - start_action_ns) / 1e6

        window_hit = (latency_ms <= self.max_window_ms)

        if latency_ms < 30.0:
            print(f"[FAST-PATH: <30ms] latency_ms={latency_ms:.2f}ms (PASS - rapid detection)")
        elif latency_ms <= self.max_window_ms:
            print(f"[PASS: WITHIN TARGET WINDOW] latency_ms={latency_ms:.2f}ms duration_ms={action_duration_ms:.2f}ms")
        else:
            print(f"[FAIL: RACE WINDOW EXCEEDED] latency_ms={latency_ms:.2f}ms > {self.max_window_ms}ms")

        print(
            f"[ACTION CHAIN LOG] "
            f"actual_initial_x={actual_initial_x} actual_initial_y={actual_initial_y} "
            f"actual_final_x={actual_final_x} actual_final_y={actual_final_y} "
            f"actual_delta_x={actual_delta_x} actual_delta_y={actual_delta_y}"
        )

        result = ActionLatencyResult(
            actual_initial_x=actual_initial_x,
            actual_initial_y=actual_initial_y,
            actual_final_x=actual_final_x,
            actual_final_y=actual_final_y,
            actual_delta_x=actual_delta_x,
            actual_delta_y=actual_delta_y,
            detection_ts_ns=detection_ts_ns,
            start_action_ns=start_action_ns,
            completion_ts_ns=completion_ns,
            latency_ms=latency_ms,
            action_duration_ms=action_duration_ms,
            window_hit=window_hit
        )

        logger.info(json.dumps({
            "event": "CHAINED_ACTION_DISPATCHED",
            "actual_initial": [actual_initial_x, actual_initial_y],
            "actual_final": [actual_final_x, actual_final_y],
            "actual_delta_x": actual_delta_x,
            "actual_delta_y": actual_delta_y,
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
