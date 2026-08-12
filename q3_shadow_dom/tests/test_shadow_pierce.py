"""
Q3 Shadow DOM & Accessibility Piercing Test Suite

Tests:
1. test_closed_shadow_dom_traversal_resilient_to_class_obfuscation
2. test_ax_tree_locator_matches_deep_pierce_target
"""

import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright

from q3_shadow_dom.framework.deep_pierce import DeepPierceLocator
from q3_shadow_dom.framework.ax_tree_locator import AXTreeLocator

DEMO_HTML = Path(__file__).parent.parent / "demo" / "index.html"
HOOK_JS = Path(__file__).parent.parent / "framework" / "closed_root_hook.js"

@pytest.fixture(scope="module")
def browser_instance():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()

def test_closed_shadow_dom_traversal_resilient_to_class_obfuscation(browser_instance):
    """Executes 10 consecutive reloads, asserting locator succeeds 10/10 times with mutating classes."""
    context = browser_instance.new_context()

    # Inject closed shadow root monkey-patch hook BEFORE page scripts run
    with open(HOOK_JS, "r") as f:
        hook_code = f.read()
    context.add_init_script(hook_code)

    page = context.new_page()
    observed_classes = set()

    for iteration in range(10):
        page.goto(f"file://{DEMO_HTML.resolve()}?iter={iteration}")

        locator = DeepPierceLocator(page)
        match = locator.locate_target_button()

        assert match.found is True
        assert match.tag_name == "button"
        assert match.data_qa_state == "unlocked-token"
        assert match.aria_label == "Authorize Ledger Funds"

        observed_classes.add(match.obfuscated_class)

        # Click target button and assert status region update
        clicked = locator.click_target_button()
        assert clicked is True

        page.wait_for_timeout(100)
        status_text = page.locator("#status-live").inner_text()
        assert "TRANSACTION AUTHORIZED BY LEDGER" in status_text

    # Assert class strings mutated across the 10 runs
    assert len(observed_classes) > 1, f"Expected dynamic class mutation across runs, got: {observed_classes}"
    context.close()

def test_ax_tree_locator_matches_deep_pierce_target(browser_instance):
    """Verifies CDP Accessibility tree locator lands on target element."""
    context = browser_instance.new_context()
    with open(HOOK_JS, "r") as f:
        context.add_init_script(f.read())

    page = context.new_page()
    page.goto(f"file://{DEMO_HTML.resolve()}")

    # AX Tree locator
    ax_locator = AXTreeLocator(page)
    ax_match = ax_locator.locate_by_role_path(target_role="button", target_name="Authorize Ledger Funds")

    assert ax_match.role == "button"
    assert ax_match.name == "Authorize Ledger Funds"
    assert ax_match.confidence_score >= 0.95

    # Deep pierce locator
    pierce_locator = DeepPierceLocator(page)
    pierce_match = pierce_locator.locate_target_button()

    assert pierce_match.aria_label == ax_match.name
    context.close()
