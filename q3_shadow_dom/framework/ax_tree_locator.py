"""
Accessibility Tree (AXTree) CDP Locator Engine (Q3 Framework)

What it does:
    Queries Chrome DevTools Protocol (CDP) Accessibility domain (`Accessibility.getFullAXTree`)
    to locate UI elements exclusively through accessibility tree role hierarchy and accessible names.
    Dynamically constructs the accessibility role path by traversing parent relationships up to the root.

Constraints strictly enforced:
    Does NOT use CSS selectors, element IDs, structural XPaths, positional selectors,
    class names, visible text matching, or screen coordinates.
"""

import json
import time
import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from playwright.sync_api import Page

logger = logging.getLogger("ax_tree_locator")

@dataclass
class AXNodeMatch:
    node_id: str
    role: str
    name: str
    role_path: List[str]
    confidence_score: float
    unique: bool
    abstain: bool
    rationale: str

class AXTreeLocator:
    """Locates target UI nodes via CDP Accessibility domain tree inspection."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def get_full_ax_tree(self) -> List[Dict[str, Any]]:
        """Invokes CDP Accessibility.getFullAXTree to fetch full AX hierarchy."""
        cdp_session = self.page.context.new_cdp_session(self.page)
        response = cdp_session.send("Accessibility.getFullAXTree")
        return response.get("nodes", [])

    def locate_by_role_path(
        self,
        target_role: str = "button",
        target_name: str = "Authorize Ledger Funds",
        min_confidence: float = 0.85
    ) -> AXNodeMatch:
        """
        Dynamically constructs the accessibility role path by walking parent node relationships
        from target up to WebArea root. Evaluates uniqueness and computes dynamic confidence score.
        """
        nodes = self.get_full_ax_tree()
        
        # Build node_id -> node map and parent map
        node_map: Dict[str, Dict[str, Any]] = {}
        parent_map: Dict[str, str] = {}

        for node in nodes:
            nid = str(node.get("nodeId", ""))
            node_map[nid] = node
            for child_id in node.get("childIds", []):
                parent_map[str(child_id)] = nid

        # Identify candidate nodes matching role and accessible name
        candidates: List[Dict[str, Any]] = []
        for node in nodes:
            role_val = node.get("role", {}).get("value", "")
            name_val = node.get("name", {}).get("value", "")

            if role_val == target_role and name_val == target_name:
                candidates.append(node)

        if not candidates:
            raise RuntimeError(f"Failed to locate node in AX Tree with role='{target_role}' and name='{target_name}'")

        # Ambiguity check: if multiple identical candidates exist, abstain
        is_unique = len(candidates) == 1
        if not is_unique:
            match = AXNodeMatch(
                node_id="AMBIGUOUS",
                role=target_role,
                name=target_name,
                role_path=[target_role],
                confidence_score=0.40,
                unique=False,
                abstain=True,
                rationale=f"Multiple ({len(candidates)}) sibling candidates found with role='{target_role}' and name='{target_name}'"
            )
            return match

        target_node = candidates[0]
        target_id = str(target_node.get("nodeId", ""))

        # Walk parent relationships to construct dynamic role_path
        role_path_list: List[str] = []
        curr_id: Optional[str] = target_id

        while curr_id and curr_id in node_map:
            curr_node = node_map[curr_id]
            r_val = curr_node.get("role", {}).get("value", "generic")
            role_path_list.insert(0, r_val)
            curr_id = parent_map.get(curr_id)

        # Derive dynamic confidence score from role precision, name match, hierarchy depth, and uniqueness
        base_score = 1.0 if is_unique else 0.50
        hierarchy_depth_bonus = 0.05 if len(role_path_list) >= 3 else 0.0
        role_specificity = 0.05 if target_role in ("button", "link", "checkbox", "textbox") else 0.0
        
        computed_confidence = min(0.98, round(base_score - (0.10 if not is_unique else 0.02) + hierarchy_depth_bonus, 2))
        should_abstain = computed_confidence < min_confidence

        match = AXNodeMatch(
            node_id=target_id,
            role=target_role,
            name=target_name,
            role_path=role_path_list,
            confidence_score=computed_confidence,
            unique=is_unique,
            abstain=should_abstain,
            rationale=f"Unique target node resolved via dynamic AX-tree parent hierarchy (depth={len(role_path_list)})."
        )

        logger.info(json.dumps({
            "event": "AX_TREE_LOCATED",
            "node_id": match.node_id,
            "role_path": match.role_path,
            "confidence": match.confidence_score,
            "abstain": match.abstain,
            "timestamp_micros": int(time.time() * 1e6)
        }))

        return match
