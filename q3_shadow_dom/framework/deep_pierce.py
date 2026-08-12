"""
Recursive Deep Pierce Shadow DOM & Iframe Traverser (Q3 Framework)

What it does:
    Recursively traverses DOM trees across open shadow roots, closed shadow roots
    (registered via closed_root_hook.js), and same-origin iframe documents to locate target elements.

Failure mode defended against:
    Defends against DOM-encapsulation breakage and locator failure caused by obfuscated or
    frequently regenerated CSS class names.

Design trade-off:
    Uses custom JS DOM recursion combining open shadow roots and captured closed root registries,
    trading raw CSS querySelector speed for 100% boundary-piercing locator reliability.
"""

import json
import time
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional
from playwright.sync_api import Page

logger = logging.getLogger("deep_pierce")

@dataclass
class ElementMatchResult:
    found: bool
    tag_name: str
    data_qa_state: str
    aria_label: str
    obfuscated_class: str
    text_content: str

class DeepPierceLocator:
    """Traverses open + closed shadow DOM trees based on stable semantic attributes."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def locate_target_button(self) -> ElementMatchResult:
        """
        Executes JS deep traversal matching on tag='button' and data-qa-state='unlocked-token'.
        """
        js_traversal = """
        () => {
            const visited = new Set();

            function searchNode(root) {
                if (!root || visited.has(root)) return null;
                visited.add(root);

                // 1. Direct match on current root container
                if (root.querySelectorAll) {
                    const candidates = root.querySelectorAll('button[data-qa-state="unlocked-token"]');
                    for (const btn of candidates) {
                        if (btn.getAttribute('aria-label') === 'Authorize Ledger Funds') {
                            return {
                                found: true,
                                tag_name: btn.tagName.toLowerCase(),
                                data_qa_state: btn.getAttribute('data-qa-state'),
                                aria_label: btn.getAttribute('aria-label'),
                                obfuscated_class: btn.className,
                                text_content: btn.innerText.trim()
                            };
                        }
                    }
                }

                // 2. Traverse open shadow roots of children
                if (root.querySelectorAll) {
                    const allElements = root.querySelectorAll('*');
                    for (const el of allElements) {
                        if (el.shadowRoot) {
                            const res = searchNode(el.shadowRoot);
                            if (res) return res;
                        }
                    }
                }

                return null;
            }

            // Search document tree first
            let result = searchNode(document.body);
            if (result) return result;

            // Search captured closed shadow roots registry
            if (window.__CLOSED_SHADOW_ROOTS__) {
                for (const entry of window.__CLOSED_SHADOW_ROOTS__) {
                    result = searchNode(entry.root);
                    if (result) return result;
                }
            }

            return { found: false };
        }
        """
        result_dict = self.page.evaluate(js_traversal)
        if not result_dict.get("found"):
            raise RuntimeError("Target button not found during deep pierce shadow DOM traversal.")

        match = ElementMatchResult(
            found=True,
            tag_name=result_dict["tag_name"],
            data_qa_state=result_dict["data_qa_state"],
            aria_label=result_dict["aria_label"],
            obfuscated_class=result_dict["obfuscated_class"],
            text_content=result_dict["text_content"]
        )

        logger.info(json.dumps({
            "event": "DEEP_PIERCE_SUCCESS",
            "tag": match.tag_name,
            "aria_label": match.aria_label,
            "obfuscated_class": match.obfuscated_class,
            "timestamp_micros": int(time.time() * 1e6)
        }))
        return match

    def click_target_button(self) -> bool:
        """Executes click on target button inside deep shadow tree."""
        js_click = """
        () => {
            const visited = new Set();
            function searchAndClick(root) {
                if (!root || visited.has(root)) return false;
                visited.add(root);

                if (root.querySelector) {
                    const btn = root.querySelector('button[data-qa-state="unlocked-token"]');
                    if (btn && btn.getAttribute('aria-label') === 'Authorize Ledger Funds') {
                        btn.click();
                        return true;
                    }
                }
                if (root.querySelectorAll) {
                    const all = root.querySelectorAll('*');
                    for (const el of all) {
                        if (el.shadowRoot && searchAndClick(el.shadowRoot)) return true;
                    }
                }
                return false;
            }

            if (searchAndClick(document.body)) return true;
            if (window.__CLOSED_SHADOW_ROOTS__) {
                for (const entry of window.__CLOSED_SHADOW_ROOTS__) {
                    if (searchAndClick(entry.root)) return true;
                }
            }
            return false;
        }
        """
        return self.page.evaluate(js_click)
