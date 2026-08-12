# Frugal Testing / BuildNexTech — AI-Native SWE Intern Submission

**Candidate:** <YOUR_NAME> · **Stack:** Python 3.11/3.12 + Playwright + Node.js 20 (Express + WS)  
**Submission Repository:** `https://github.com/vaishnavitelaprolu30/frugal.git`

---

## 1. Executive Summary & Architecture

This repository contains the complete practical implementation, testbeds, automation frameworks, test suites, architectural answers, and research article for the Frugal Testing / BuildNexTech AI-Native SWE Intern submission.

```
frugal/
├── README.md                     # Architecture, run commands, trade-offs, deviations
├── PROMPTS.md                    # Curated GenAI prompt history & iteration log
├── master_dashboard.js           # Master Express control center (:8000) for running testbeds & Pytest
├── requirements.txt              # Pinned Python dependencies (playwright, pytest, pytest-html, pytest-asyncio)
├── package.json                  # Node dependencies for micro-testbeds (express, ws)
├── pytest.ini                    # Pytest configuration & test discovery settings
│
├── q1_canvas_race/               # Q1 Canvas Terminal & WebSocket Race Automation (15 pts)
│   ├── testbed/                  # Express + WS 6x4 canvas streaming server (:8081)
│   ├── framework/                # Real WS route interceptor (page.route_web_socket), rAF pixel engine, circuit breaker
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
PYTHONPATH=. pytest q1_canvas_race/tests/test_canvas_race.py -v --html=q1_canvas_race/artifacts/report.html
```

---

### Executing Q2: HMAC Replay Attack & API Gateway

```bash
# Terminal 1: Start Mock Gateway (:8082)
npm run start:q2

# Terminal 2: Run Q2 Pytest Suite (Executes both SECURE and VULNERABLE mode tests)
PYTHONPATH=. pytest q2_crypto_replay/tests/test_replay_chain.py -v
```

---

### Executing Q3: Shadow DOM Piercing & AX Tree Locator

```bash
# Run Q3 Pytest Resilience Suite (10 consecutive reloads with dynamic class mutation)
PYTHONPATH=. pytest q3_shadow_dom/tests/test_shadow_pierce.py -v
```

---

### Running Master Dashboard & Master Test Suite

```bash
# Start Unified Master Control Center on http://localhost:8000
node master_dashboard.js

# Run Full Test Suite Across All Modules
PYTHONPATH=. pytest -v
```

---

## 3. Engineering Implementation Details & Trade-Offs

### Q1 — Canvas & WebSocket Race Condition (15 Points)
- **Real WebSocket Interception (`page.route_web_socket()`)**: Intercepts `ws://localhost:8081/stream`, applying non-blocking frame holding for exact Fibonacci delays (`min(1000 * fib(step), 8000.0)`) and forwarding mutated JSON payloads directly in stream.
- **Genuine Pixel-Based Calibration**: Scans horizontal and vertical lines in a `requestAnimationFrame` loop, detecting RGB color discontinuities between canvas background `[2, 6, 23]` and rendered cell fills. Zero hardcoded geometry literals.
- **Race Timing Instrumentation**: Measures reaction latency from transition detection (`T_detection`) to the START of the hover action (`T_action_start`), enforcing `race_latency_ms <= 100.0`.
- **Circuit Breaker Recovery**: Fails attempts 1 & 2 on coordinate drift, triggers recalibration pass, and succeeds on attempt 3 returning value with state `CLOSED`. Separate exhaustion test verifies transition to `OPEN`.

### Q2 — Nonce-Guarded HMAC Gateway & Replay Suite (4 Points)
- **Real Vulnerable Gateway Replay**: Interacts with mock gateway in `GATEWAY_MODE=VULNERABLE`, dispatches POST -> signed PUT -> exact replay, observing duplicate 2xx success and emitting `VULNERABILITY_ALERT.json` with CWE-294 details.
- **Replay Timing Gap**: Measures `replay_gap_micros` from PUT 1 completion to PUT 2 dispatch, enforcing `<150ms`.
- **Canonical HMAC-SHA512**: Strictly orders JSON keys (`separators=(',', ':')`) and signs with challenge token + timestamp.

### Q3 — Closed Shadow DOM Piercing & AX Tree (1 Point + CoT)
- **Deep Shadow DOM Piercing**: Intercepts `attachShadow` via pre-load script hook into global registry.
- **CDP AX Tree Locator**: Queries `Accessibility.getFullAXTree`, constructs parent pointers dynamically to generate role-paths up to `WebArea`, and derives dynamic confidence scores.
- **`test_canvas_race.py`** – High-precision integration suite executing full UI-level race.
   - Converts Playwright to **100% asynchronous execution** (`async_playwright`) to support non-blocking Fibonacci WebSocket holding.
   - Injects the `WSChaosInterceptor` dynamically and verifies the chained action (hover -> drag -> click) executes in under 100ms.
   - Evaluates real 8000ms max jitter.

---

## 4. Final Verification Matrix

| Requirement | Implementation Module | Verification Method | Status |
| :--- | :--- | :--- | :--- |
| **Q1 Real WS Route Interception** | `q1_canvas_race/framework/ws_chaos.py` | Playwright `page.route_web_socket` frame holding | **PASSED** |
| **Q1 Fibonacci Jitter (8000ms Cap)** | `q1_canvas_race/framework/ws_chaos.py` | Steps 1..10 unit test (`test_fibonacci_jitter_sequence_formula`) | **PASSED** |
| **Q1 Dynamic Pixel Calibration** | `q1_canvas_race/framework/pixel_engine.py` | rAF RGB discontinuity scan + canvas resize test (`1440x900`) | **PASSED** |
| **Q1 Corrupted Payload Stream Mutation**| `q1_canvas_race/tests/test_canvas_race.py` | Stream route payload mutation (`1e+7`) & silent corruption assertion | **PASSED** |
| **Q1 Circuit Breaker Recovery** | `q1_canvas_race/framework/circuit_breaker.py` | Flaky action recovery (attempt 3) & exhaustion suite | **PASSED** |
| **Q1 Race Latency Instrumentation** | `q1_canvas_race/framework/chained_actions.py` | Reaction latency to START of hover (`<= 100ms`, 20-run summary) | **PASSED** |
| **Q2 Real Vulnerable Replay Test** | `q2_crypto_replay/tests/test_replay_chain.py` | Real duplicate 2xx observation against `VULNERABLE` gateway | **PASSED** |
| **Q2 Replay Timing Measurement** | `q2_crypto_replay/framework/chain_client.py` | PUT 1 completion -> PUT 2 dispatch timing (`<150ms`) | **PASSED** |
| **Q3 Dynamic AX Role-Path** | `q3_shadow_dom/framework/ax_tree_locator.py` | CDP `Accessibility.getFullAXTree` parent hierarchy walk | **PASSED** |
| **Zero Static Delays** | Repository Wide | `grep -rn "time.sleep"` validation (0 static delays) | **PASSED** |
