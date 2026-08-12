# GenAI Prompt Engineering Audit Log (`PROMPTS.md`)

**Repository:** `frugal-testing-ainative` · **Owner:** <YOUR_NAME>  
**Purpose:** Honest record of prompts fed to Antigravity AI, capturing initial prompts, failed attempts, diagnostic corrections, and final prompt refinements.

---

## 1. Master Project Brief Prompt

### Initial System Prompt
```text
# ROLE: Senior SDET / AI-Native Automation Architect
Building take-home submission for AI-Native SWE Intern role at Frugal Testing.
Constraints: Python 3.11/3.12 + Playwright sync API + pytest. Local Node.js testbeds.
ZERO static sleeps. All element states must be driven by observed transitions or canvas pixel colors.
Deterministic, reproducible, type hints on every function, custom exception hierarchy, structured JSON logging.
```

---

## 2. Phase 1 & 2: Q1 Canvas & WebSocket Race Condition

### Initial Prompt
```text
Build Q1 Express + WebSocket testbed on port 8081 streaming a 6x4 canvas terminal.
Build Playwright automation framework with Fibonacci jitter, rAF pixel engine sampling getImageData, circuit breaker, and chained action dispatcher (hover -> drag 15px -> click) within 30-100ms window.
```

### Failed Attempt / Course Correction
- **Issue Discovered:** Initial AI proposal used static pixel coordinates `[100, 200]` hardcoded into Python script.
- **Diagnostic Correction Prompt:**
```text
REJECT: Hardcoded canvas pixel coordinates violate Constraint 3. Canvas coordinates must be dynamically derived via a calibration scan that locates grid cell boundaries from pixel color gradients. Implement pixel_engine.calibrate() to return dynamic coordinates.
```
- **Outcome:** Added dynamic JS calibration pass in `pixel_engine.py` that computes grid offsets automatically.

---

## 3. Phase 3: Q2 HMAC Gateway & Replay Attack Suite

### Initial Prompt
```text
Build Q2 Express mock gateway on port 8082 supporting POST /v1/transactions (returns X-Transaction-Id in header) and PUT /v1/transactions/:id with HMAC-SHA512 header validation and nonce replay protection. Support SECURE and VULNERABLE modes.
```

### Failed Attempt / Course Correction
- **Issue Discovered:** Python HMAC signer generated JSON string with default spacing (`{"action": "TRANSFER", "amount": 500.0}`), causing gateway verification to fail with HTTP 401 due to signature mismatch.
- **Diagnostic Correction Prompt:**
```text
FAIL DIAGNOSIS: Signature mismatch on PUT /v1/transactions. Python client JSON serialization contains spaces after colons, whereas Node.js server parses strict canonical JSON. Enforce json.dumps(body, sort_keys=True, separators=(',', ':')) in hmac_signer.py.
```
- **Outcome:** Signatures matched byte-for-byte across runtimes.

---

## 4. Phase 4: Q3 Closed Shadow DOM & CoT Prompt

### Initial Prompt
```text
Build Q3 demo page with nested open->closed->open shadow DOM and obfuscated class names.
Create closed_root_hook.js monkey-patching attachShadow, deep_pierce.py, ax_tree_locator.py via CDP session, and COT_SYSTEM_PROMPT.md.
```

### Prompt Refinement for CoT Prompt
- **Refinement Prompt:**
```text
Ensure COT_SYSTEM_PROMPT.md explicitly forbids CSS selectors, element IDs, structural XPaths, nth-child indexing, and visual coordinates. Require a strict 6-step reasoning sequence, confidence scoring, 2 positive worked examples, 1 negative abstain example, and strict JSON output schema.
```
- **Outcome:** Produced production-grade Chain-of-Thought prompt document in `q3_shadow_dom/COT_SYSTEM_PROMPT.md`.

---

## 5. Phase 5 & 6: Section B Answers & Q21 MCP Sandbox Article

### Prompt Strategy
- Individual scenario questions (Q4–Q20) drafted one at a time, enforcing hard maximum of 150 words per response, concrete metrics, specific protocols, and explicit failure modes/trade-offs.
- Q21 article drafted on Topic B (MCP Sandboxes) with complete threat model, rigid schema designs, `execve` argv execution wrapper, defense-in-depth, and trade-offs.
