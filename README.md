# Frugal Testing / BuildNexTech — AI-Native SWE Intern Submission

**Candidate:** Nandan Perumalla · **Stack:** Python 3.11/3.12 + Playwright + Node.js 20 (Express + WS)  
**Submission Repository:** `frugal-testing-ainative`

---

## 1. Executive Summary & Architecture

This repository contains the complete practical implementation, testbeds, automation frameworks, test suites, architectural answers, and research article for the Frugal Testing / BuildNexTech AI-Native SWE Intern submission.

```
frugal-testing-ainative/
├── README.md                     # Architecture, run commands, trade-offs, deviations
├── PROMPTS.md                    # Curated GenAI prompt history & iteration log
├── requirements.txt              # Pinned Python dependencies (playwright, pytest, pytest-html)
├── package.json                  # Node dependencies for micro-testbeds (express, ws)
├── pytest.ini                    # Pytest configuration & test discovery settings
│
├── q1_canvas_race/               # Q1 Canvas Terminal & WebSocket Race Automation (15 pts)
│   ├── testbed/                  # Express + WS 6x4 canvas streaming server (:8081)
│   ├── framework/                # Fibonacci jitter, rAF pixel engine, circuit breaker, action dispatcher
│   ├── tests/                    # Pytest suite with dual error boundary verification
│   └── artifacts/                # Timing CSVs, HTML reports, screenshots
│
├── q2_crypto_replay/             # Q2 Nonce-Guarded HMAC Gateway & Replay Suite (4 pts)
│   ├── mock_gateway/             # Express HMAC-SHA512 gateway server (:8082, SECURE | VULNERABLE modes)
│   ├── framework/                # Canonical HMAC signer, API chain client, vulnerability reporter
│   ├── tests/                    # Pytest suite testing HMAC verification & replay guards
│   └── artifacts/                # Replay timing metrics & VULNERABILITY_ALERT.json
│
├── q3_shadow_dom/                # Q3 Closed Shadow DOM Piercing & CoT Prompt (1 pt + CoT)
│   ├── demo/                     # HTML view with open->closed->open shadow DOM & obfuscated classes
│   ├── framework/                # attachShadow init script hook, deep pierce locator, CDP AX tree locator
│   ├── COT_SYSTEM_PROMPT.md      # CoT System Prompt for LLM AX-Tree locator engine
│   └── tests/                    # Dynamic class mutation resilience suite (10 reloads)
│
└── docs/
    ├── SECTION_B_ANSWERS.md      # Section 0 declarations + Q4–Q20 technical answers (70 pts)
    ├── Q21_ARTICLE.md            # Technical article: Securing AI Workspaces with MCP Sandboxes (5 pts)
    └── SUBMISSION_CHECKLIST.md   # PDF & submission compliance verification checklist
```

---

## 2. Quick Start & Execution Guide

### Prerequisites
- Node.js >= 18.0.0
- Python >= 3.11
- Playwright Chromium browser installed

### Environment Setup
```bash
# 1. Install Node.js dependencies
npm install

# 2. Setup Python virtual environment & dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

---

### Executing Q1: Canvas & WebSocket Race Condition Automation

```bash
# Terminal 1: Start Q1 Canvas & WS Server (:8081)
npm run start:q1

# Terminal 2: Run Q1 Pytest Suite
pytest q1_canvas_race/tests/test_canvas_race.py -v --html=q1_canvas_race/artifacts/report.html
```

---

### Executing Q2: HMAC Replay Attack & API Gateway

```bash
# SECURE MODE TEST RUN:
# Terminal 1: Start Mock Gateway in SECURE Mode (:8082)
GATEWAY_MODE=SECURE npm run start:q2

# Terminal 2: Run Q2 Pytest Suite (Asserts HTTP 409 Conflict on replay)
pytest q2_crypto_replay/tests/test_replay_chain.py -v

# VULNERABLE MODE TEST RUN:
# Terminal 1: Start Mock Gateway in VULNERABLE Mode (:8082)
GATEWAY_MODE=VULNERABLE npm run start:q2

# Terminal 2: Run Q2 Pytest Suite (Asserts vulnerability alert emission)
pytest q2_crypto_replay/tests/test_replay_chain.py -v
```

---

### Executing Q3: Shadow DOM Piercing & AX Tree Locator

```bash
# Run Q3 Pytest Resilience Suite (10 consecutive reloads with dynamic class mutation)
pytest q3_shadow_dom/tests/test_shadow_pierce.py -v
```

---

### Running Full Test Suite Across All Modules

```bash
pytest -v
```

---

## 3. Engineering Trade-Offs & Known Deviations

### Engineering Trade-Offs

1. **Client-Side Canvas Pixel Inspection (Q1):**  
   We chose browser-injected `getImageData` pixel classification inside a `requestAnimationFrame` loop over server-side image diffing.  
   *Trade-Off:* Minimal browser JS evaluation overhead (~1.2ms) in exchange for exact paint-level state determination immune to DOM locator spoofing.

2. **Canonical JSON Serialization (Q2):**  
   Strict key sorting with zero whitespace (`separators=(',', ':')`) was selected for HMAC calculation.  
   *Trade-Off:* Sacrifices formatting flexibility for 100% cryptographic reproducibility across Python and Node.js runtimes.

3. **Monkey-Patched `attachShadow` Hook (Q3):**  
   A pre-load `page.add_init_script()` hook intercepts closed shadow roots into a registry.  
   *Trade-Off:* This is a test-harness affordance used specifically during automation setup, enabling 100% reliable boundary piercing without altering production application source code.

### Known Deviations

- **Microsecond Timing under Non-Realtime OS Constraints:**  
  While the client measures action latency using sub-millisecond high-resolution timers (`perf_counter_ns`), real-world OS scheduler jitter on non-realtime operating systems (macOS/Linux) can introduce microsecond-level variance during parallel test execution. All latency assertions enforce defensible tolerance bands (30–100ms for Q1, <150ms for Q2).
