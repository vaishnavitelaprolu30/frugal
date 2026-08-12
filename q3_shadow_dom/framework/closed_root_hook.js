/**
 * Closed Shadow Root Attachment Hook (Q3 Framework)
 *
 * What it does:
 *   Monkey-patches Element.prototype.attachShadow BEFORE page script execution to intercept
 *   and record references to all created shadow roots (including mode: 'closed').
 *
 * Why it exists:
 *   Closed shadow DOM roots intentionally encapsulate DOM nodes from `element.shadowRoot` calls.
 *   In automation, capturing the root reference at initialization time is the only reliable,
 *   specification-compliant way to traverse sealed boundaries without modifying application source code.
 *
 * Safety / Scope:
 *   This is a test-harness affordance injected strictly during automation fixture setup.
 */

(function() {
  if (window.__CLOSED_SHADOW_HOOK_INSTALLED__) return;
  window.__CLOSED_SHADOW_HOOK_INSTALLED__ = true;

  window.__CLOSED_SHADOW_ROOTS__ = [];
  const originalAttachShadow = Element.prototype.attachShadow;

  Element.prototype.attachShadow = function(init) {
    const shadowRoot = originalAttachShadow.call(this, init);
    try {
      window.__CLOSED_SHADOW_ROOTS__.push({
        host: this,
        root: shadowRoot,
        mode: init ? init.mode : 'unknown',
        timestamp: performance.now()
      });
    } catch (e) {
      console.warn('[ClosedRootHook] Failed to register shadow root:', e);
    }
    return shadowRoot;
  };

  console.log('[ClosedRootHook] Element.prototype.attachShadow successfully hooked.');
})();
