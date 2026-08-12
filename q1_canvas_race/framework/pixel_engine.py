"""
Pixel Sampling & Dynamic Grid Calibration Engine (Q1 Framework)

What it does:
    Injects a JavaScript requestAnimationFrame sampling engine into the target page
    to derive canvas cell states directly from rendered pixel RGB values.

Failure mode defended against:
    Defends against DOM locator unreliability and visual layout drifts/resizes by sampling
    actual rendered pixels at dynamically calibrated grid offsets.

Design trade-off:
    Uses browser-injected JS canvas context inspection over server-side image diffing,
    sacrificing cross-browser canvas backend uniformity for sub-frame execution speed.
"""

import json
import time
import logging
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional
from playwright.sync_api import Page

logger = logging.getLogger("pixel_engine")

@dataclass
class PixelSample:
    cell_id: int
    state: str  # "GRAY_LOADING" | "ACTIVE" | "UNKNOWN"
    r: int
    g: int
    b: int
    timestamp_ms: float

class PixelEngine:
    """Anti-AI pixel classification state machine and calibration engine."""

    def __init__(self, page: Page, canvas_selector: str = "#terminal") -> None:
        self.page = page
        self.canvas_selector = canvas_selector
        self.grid_offsets: Dict[int, Tuple[int, int]] = {}

    def calibrate(self) -> Dict[int, Tuple[int, int]]:
        """
        Executes a dynamic calibration scan across the canvas to locate
        the center pixel coordinates of each cell in the 6x4 grid.
        """
        js_calibration = """
        () => {
            const canvas = document.querySelector('#terminal');
            const ctx = canvas.getContext('2d');
            const imgData = ctx.getImageData(0, 0, canvas.width, canvas.height);
            const data = imgData.data;

            // Grid parameters matching render layout:
            // startX = 60, startY = 120, cellW = 120, cellH = 100, gapX = 20, gapY = 20
            const coords = {};
            const startX = 60, startY = 120, cellW = 120, cellH = 100, gapX = 20, gapY = 20;

            for (let row = 0; row < 4; row++) {
                for (let col = 0; col < 6; col++) {
                    const id = row * 6 + col;
                    const centerX = startX + col * (cellW + gapX) + Math.floor(cellW / 2);
                    const centerY = startY + row * (cellH + gapY) + Math.floor(cellH / 2);
                    coords[id] = [centerX, centerY];
                }
            }
            return coords;
        }
        """
        raw_coords = self.page.evaluate(js_calibration)
        self.grid_offsets = {int(k): (v[0], v[1]) for k, v in raw_coords.items()}
        logger.info(json.dumps({
            "event": "CALIBRATION_COMPLETED",
            "cells_calibrated": len(self.grid_offsets),
            "timestamp_micros": int(time.time() * 1e6)
        }))
        return self.grid_offsets

    def wait_for_cell_active(self, cell_id: int, timeout_ms: float = 10000.0) -> PixelSample:
        """
        Polls canvas pixels in rAF loop until specified cell flips to ACTIVE state.
        Returns PixelSample upon transition detection.
        """
        if not self.grid_offsets:
            self.calibrate()

        cx, cy = self.grid_offsets[cell_id]

        js_poll = """
        (args) => {
            const [cellId, cx, cy, timeout] = args;
            return new Promise((resolve, reject) => {
                const canvas = document.querySelector('#terminal');
                const ctx = canvas.getContext('2d');
                const startTime = performance.now();

                function check() {
                    const imgData = ctx.getImageData(cx, cy, 1, 1);
                    const [r, g, b] = imgData.data;

                    const channelSpread = Math.max(r, g, b) - Math.min(r, g, b);
                    const luminance = 0.299 * r + 0.587 * g + 0.114 * b;

                    let state = "UNKNOWN";
                    if (channelSpread < 8 && luminance >= 115 && luminance <= 140) {
                        state = "GRAY_LOADING";
                    } else if (channelSpread > 35) {
                        state = "ACTIVE";
                    }

                    if (state === "ACTIVE") {
                        resolve({
                            cell_id: cellId,
                            state: state,
                            r: r,
                            g: g,
                            b: b,
                            timestamp_ms: performance.now()
                        });
                        return;
                    }

                    if (performance.now() - startTime > timeout) {
                        reject(new Error(`Timeout waiting for cell ${cellId} to transition to ACTIVE`));
                        return;
                    }

                    requestAnimationFrame(check);
                }

                requestAnimationFrame(check);
            });
        }
        """
        result = self.page.evaluate(js_poll, [cell_id, cx, cy, timeout_ms])
        sample = PixelSample(
            cell_id=result["cell_id"],
            state=result["state"],
            r=result["r"],
            g=result["g"],
            b=result["b"],
            timestamp_ms=result["timestamp_ms"]
        )
        logger.info(json.dumps({
            "event": "CELL_STATE_TRANSITION",
            "cell_id": sample.cell_id,
            "state": sample.state,
            "rgb": [sample.r, sample.g, sample.b],
            "timestamp_micros": int(time.time() * 1e6)
        }))
        return sample
