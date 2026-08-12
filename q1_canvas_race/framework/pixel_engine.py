"""
Pixel Sampling & Dynamic Grid Calibration Engine (Q1 Framework)

What it does:
    Injects a JavaScript requestAnimationFrame sampling engine into the target page
    to derive canvas cell boundaries and center coordinates directly from rendered pixel RGB values.

Failure mode defended against:
    Defends against DOM locator unreliability and visual layout drifts/resizes by sampling
    actual rendered pixels and dynamically detecting RGB color discontinuities.

Requirements:
    - Zero hardcoded startX/startY/cellW/cellH/gapX/gapY literals.
    - Scans horizontal and vertical pixel lines in rAF loop until cell boundaries are detected.
    - Returns derived grid coordinates and boundary metadata for inspectability.
"""

import json
import time
import logging
from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional, List
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
    """Anti-AI pixel classification state machine and dynamic calibration engine."""

    def __init__(self, page: Page, canvas_selector: str = "#terminal") -> None:
        self.page = page
        self.canvas_selector = canvas_selector
        self.grid_offsets: Dict[int, Tuple[int, int]] = {}
        self.detected_boundaries: Dict[str, Any] = {}

    def calibrate(self, timeout_ms: float = 15000.0) -> Dict[int, Tuple[int, int]]:
        """
        Executes a dynamic pixel calibration scan across the canvas in a rAF loop to derive
        column and row boundaries from RGB color discontinuities, returning
        derived cell centers and boundary metadata.
        """
        js_calibration = """
        (timeoutMs) => {
            return new Promise((resolve, reject) => {
                const canvas = document.querySelector("#terminal") || document.querySelector("canvas");
                if (!canvas) {
                    reject(new Error("Canvas element not found"));
                    return;
                }

                const ctx = canvas.getContext("2d");
                const w = canvas.width;
                const h = canvas.height;
                const startTime = performance.now();

                function scan() {
                    const imgData = ctx.getImageData(0, 0, w, h);
                    const data = imgData.data;

                    function getRGB(x, y) {
                        const px = Math.min(Math.max(Math.floor(x), 0), w - 1);
                        const py = Math.min(Math.max(Math.floor(y), 0), h - 1);
                        const idx = (py * w + px) * 4;
                        return [data[idx], data[idx + 1], data[idx + 2]];
                    }

                    const bg = getRGB(30, Math.min(170, Math.floor(h * 0.3)));

                    function isCellPixel(x, y) {
                        const [r, g, b] = getRGB(x, y);
                        const dist = Math.abs(r - bg[0]) + Math.abs(g - bg[1]) + Math.abs(b - bg[2]);
                        return dist > 35;
                    }

                    const rowStarts = [], rowEnds = [];
                    let inCell = false;
                    for (let y = Math.floor(h * 0.18); y < h; y++) {
                        const cell = isCellPixel(Math.floor(w * 0.125), y);
                        if (cell && !inCell) { inCell = true; rowStarts.push(y); }
                        else if (!cell && inCell) { inCell = false; rowEnds.push(y); }
                    }
                    if (inCell) rowEnds.push(h);

                    const rows = [];
                    for (let i = 0; i < rowStarts.length; i++) {
                        if (rowEnds[i] - rowStarts[i] >= 30) {
                            rows.push([rowStarts[i], rowEnds[i]]);
                        }
                    }

                    if (rows.length >= 1) {
                        const scanY = Math.floor((rows[0][0] + rows[0][1]) / 2);
                        const colStarts = [], colEnds = [];
                        inCell = false;
                        for (let x = 0; x < w; x++) {
                            const cell = isCellPixel(x, scanY);
                            if (cell && !inCell) { inCell = true; colStarts.push(x); }
                            else if (!cell && inCell) { inCell = false; colEnds.push(x); }
                        }
                        if (inCell) colEnds.push(w);

                        const cols = [];
                        for (let i = 0; i < colStarts.length; i++) {
                            if (colEnds[i] - colStarts[i] >= 30) {
                                cols.push([colStarts[i], colEnds[i]]);
                            }
                        }

                        if (cols.length >= 1) {
                            const coords = {};
                            for (let r = 0; r < rows.length; r++) {
                                for (let c = 0; c < cols.length; c++) {
                                    const id = r * cols.length + c;
                                    const cx = Math.floor((cols[c][0] + cols[c][1]) / 2);
                                    const cy = Math.floor((rows[r][0] + rows[r][1]) / 2);
                                    coords[id] = [cx, cy];
                                }
                            }
                            resolve({
                                coords: coords,
                                boundaries: { cols: cols, rows: rows }
                            });
                            return;
                        }
                    }

                    if (performance.now() - startTime > timeoutMs) {
                        reject(new Error("Calibration timeout waiting for grid rendering"));
                        return;
                    }

                    requestAnimationFrame(scan);
                }

                requestAnimationFrame(scan);
            });
        }
        """
        res = self.page.evaluate(js_calibration, timeout_ms)
        raw_coords = res.get("coords", {})
        self.detected_boundaries = res.get("boundaries", {})
        self.grid_offsets = {int(k): (v[0], v[1]) for k, v in raw_coords.items()}

        print(f"[PIXEL ENGINE CALIBRATED] derived_cells={len(self.grid_offsets)} cols={self.detected_boundaries.get('cols')} rows={self.detected_boundaries.get('rows')}")

        logger.info(json.dumps({
            "event": "DYNAMIC_CALIBRATION_COMPLETED",
            "cells_calibrated": len(self.grid_offsets),
            "boundaries": self.detected_boundaries,
            "timestamp_micros": int(time.time() * 1e6)
        }))
        return self.grid_offsets

    def wait_for_cell_active(self, cell_id: int, timeout_ms: float = 10000.0) -> PixelSample:
        """
        Polls canvas pixels in rAF loop until specified cell flips to ACTIVE state.
        Returns PixelSample upon transition detection.
        """
        if not self.grid_offsets:
            self.calibrate(timeout_ms)

        if cell_id not in self.grid_offsets:
            self.calibrate(timeout_ms)

        cx, cy = self.grid_offsets[cell_id]

        js_poll = """
        (args) => {
            const [cellId, cx, cy, timeout] = args;
            return new Promise((resolve, reject) => {
                const canvas = document.querySelector('#terminal') || document.querySelector('canvas');
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
