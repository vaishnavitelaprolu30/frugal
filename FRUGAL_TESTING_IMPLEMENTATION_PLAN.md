# Frugal Testing / BuildNexTech — AI-Native SWE Intern
## Master Implementation Plan + Antigravity Prompt Pack

**Owner:** Nandan Perumalla · **Stack:** Python 3.11 + Playwright + Node/Express testbeds
**Window:** 32 hours · **Submission:** one unified PDF + 3 Drive folders + 1 video CV

---

## 0. Read this before you prompt anything

### Where the marks actually are

| Item | Points | Effort share |
|---|---|---|
| Q1 Canvas / WebSocket automation | 15 | ~35% |
| Q2 HMAC replay API testing | 4 | ~10% |
| Q3 Shadow DOM + CoT prompt | 1 | ~5% |
| Q4–Q20 scenarios (14 × 5) | 70 | ~30% |
| Q21 article | 5 | ~10% |
| Q23 video CV | 5 | ~10% |
| Section 0 + Q22 | gate | must-do |

**Section B is 70 points — more than all of Section A combined.** Most candidates over-invest in code and hand in thin, generic scenario answers. Do not do that. Budget real hours for Q4–Q20.

### The three things that will make you stand out

1. **You build the testbeds, not just the tests.** The PDF admits public sites can't be used (TradingView blocks it, Restful Booker has no nonces). Ninety percent of candidates will fake a demo or hand-wave. You will ship a real WebSocket canvas streaming server and a real HMAC/nonce API gateway, then automate against them. That's two working systems instead of two scripts.
2. **Your failure paths actually fire.** Build a `--vulnerable` toggle into the mock server so the video shows both the *secure* path (409 rejected) and the *broken* path (200 OK → framework screams `CRITICAL DATA-MUTATION VULNERABILITY`). Demonstrating the assertion catching a real bug is worth more than a green checkmark.
3. **A curated `PROMPTS.md`.** They explicitly demand prompt history on video. Keep a running, honest log of the prompts you fed Antigravity — including the ones that failed and how you corrected them. Scroll it on camera. It directly answers their "AI-Native" thesis.

### Honest flag before you start

Section 0 asks you to consent to a **36-month bond including a 12-month internship**, and confirm stipend/CTC details you say you've received. That's a long commitment for a 2027 graduate — worth a clear-eyed decision before you sink 32 hours in, not after. It doesn't change the plan; just don't answer Q1–Q6 of Section 0 on autopilot.

---

## 1. Repository structure

Create one repo, three deliverable folders are exported from it.

```
frugal-testing-ainative/
├── README.md                     # architecture, how to run, design trade-offs
├── PROMPTS.md                    # curated GenAI prompt history (video artifact)
├── requirements.txt
├── package.json
├── pytest.ini
│
├── q1_canvas_race/
│   ├── testbed/
│   │   ├── server.js             # Express + ws broadcaster (candles + gray→active states)
│   │   ├── public/index.html     # HTML5 canvas terminal, zero semantic DOM
│   │   └── public/terminal.js    # rAF render loop, gray loading → active colour
│   ├── framework/
│   │   ├── ws_chaos.py           # Fibonacci jitter + payload mutation interceptor
│   │   ├── pixel_engine.py       # rAF pixel-colour state machine (injected JS)
│   │   ├── circuit_breaker.py    # retry/offset-recalibration macro
│   │   └── chained_actions.py    # hover → drag 15px → click, 30–100ms window
│   ├── tests/test_canvas_race.py
│   └── artifacts/                # HTML report, screenshots, timing CSV
│
├── q2_crypto_replay/
│   ├── mock_gateway/
│   │   ├── server.js             # challenge tokens, HMAC-SHA512, nonce store, replay guard
│   │   └── config.js             # SECURE | VULNERABLE mode switch
│   ├── framework/
│   │   ├── hmac_signer.py
│   │   ├── chain_client.py       # POST → extract header ID → PUT → replay
│   │   └── vuln_reporter.py      # high-risk alert emitter
│   ├── tests/test_replay_chain.py
│   └── artifacts/
│
├── q3_shadow_dom/
│   ├── demo/index.html           # nested open→closed→open shadow, regenerating classes
│   ├── framework/
│   │   ├── closed_root_hook.js   # attachShadow monkey-patch (init script)
│   │   ├── deep_pierce.py        # recursive open+closed+iframe traversal
│   │   └── ax_tree_locator.py    # accessibility-tree pathing (role/name/state)
│   ├── COT_SYSTEM_PROMPT.md      # the deliverable prompt
│   └── tests/test_shadow_pierce.py
│
└── docs/
    ├── SECTION_B_ANSWERS.md
    ├── Q21_ARTICLE.md
    └── SUBMISSION_CHECKLIST.md
```

---

## 2. The Master Prompt for Antigravity

Paste this **once** as the opening instruction / project brief. Then run the phase prompts in Section 3 one at a time — do not ask an agent to do all 23 questions in a single shot; it will produce shallow output and you'll lose the 70-point section.

````text
# ROLE
You are a senior SDET / AI-native automation architect. You are building a graded
take-home submission for an "AI-Native Software Engineer Intern" role at Frugal
Testing. The evaluator is a testing company: they will read the source code, watch a
screen recording of it running, and score structural engineering judgement — not
volume of code.

# NON-NEGOTIABLE CONSTRAINTS
1. Language/stack: Python 3.11 + Playwright (sync API) + pytest for all automation.
   Local testbeds in Node.js 20 (Express + ws). No Java, no Selenium.
2. ZERO static sleeps in test logic. No time.sleep(), no
   page.wait_for_timeout(), no arbitrary polling intervals as a substitute for state.
   Every wait must be driven by an observed state transition. Deliberate latency
   injection inside the network-interception layer is the ONE exception and must be
   labelled as fault injection, not synchronisation.
3. No bounding-box or visibility-based checks in Q1. Element state must be derived
   from canvas pixel colour sampled inside a requestAnimationFrame loop.
4. Everything must run offline against locally hosted testbeds. No dependency on
   third-party live sites, no anti-bot circumvention, no traffic to systems we don't
   own. All security testing (replay, HMAC, injection) targets our own mock server.
5. Deterministic and reproducible: fixed random seeds, pinned dependency versions,
   one-command startup per question.

# ENGINEERING STANDARDS
- Type hints on every function; dataclasses for structured state.
- Every module opens with a docstring stating: what it does, what failure mode it
  defends against, and the design trade-off chosen.
- Structured logging (JSON lines) with monotonic timestamps to microsecond precision.
  Timing claims in the video must be provable from logs.
- Custom exception hierarchy. Never swallow an exception silently.
- Each test emits an artifact: HTML report + screenshots + a timing CSV.
- Config via a single dataclass per question, not scattered constants.

# OUTPUT DISCIPLINE
- Produce complete, runnable files. No "..." placeholders, no TODO stubs.
- After each file, state in one line: the design trade-off you made and what you
  rejected.
- If a spec requirement is physically impossible as literally written (e.g. an exact
  150ms guarantee on a non-realtime OS), implement the closest defensible
  engineering equivalent, then say so explicitly in a `## Known Deviations` section
  of the README. Do not silently fudge it. Honest deviation notes score better with a
  testing company than fake precision.
- Never invent library APIs. If unsure whether a Playwright method exists in the
  installed version, verify against the installed package before using it.

# WORKFLOW
Work in phases. After each phase: run the suite, paste real terminal output, and stop
for review before starting the next phase. Do not proceed on unverified code.
````

---

## 3. Phase prompts (run in order)

### Phase 1 — Q1 testbed (target: 2h)

````text
PHASE 1: Build the Q1 canvas streaming testbed under q1_canvas_race/testbed/.

server.js — Node + Express + `ws`:
- Serves ./public on :8081, WebSocket on ws://localhost:8081/stream
- On connect: sends 12 frames of {"phase":"loading"} then transitions to live data
- Live frames every 40ms: {"seq":n,"t":epochMicros,"symbol":"FRGL","price":float,
  "delta":float,"cells":[{"id":n,"x":n,"y":n,"state":"loading|active","v":float}]}
- A 6x4 grid of cells. Each cell independently flips loading -> active on a
  seeded schedule so the transition moment is deterministic across runs.
- Accepts a `?seed=` query param so runs are byte-identical for the recording.

public/index.html — a single <canvas id="terminal" width="960" height="640">.
CRITICAL: no other semantic DOM. No divs with data attributes, no text nodes
describing state. The canvas must be the only source of truth. This is what makes
the exercise DOM-locator-proof.

public/terminal.js:
- requestAnimationFrame render loop
- loading cells render in gray #808080 (+/- 3 per channel dither)
- active cells render in #16A34A (up) or #DC2626 (down)
- draws a price ticker into the canvas via fillText (pixels, not DOM)
- exposes window.__TERMINAL_STATE__ = {frameCount, lastSeq, renderTs} for telemetry
  ONLY — tests must not use it for synchronisation, only for post-hoc log correlation
- renders a red error banner + sets a canvas-drawn "ERR" glyph if it receives a
  non-finite / out-of-domain price. THIS IS THE ERROR BOUNDARY the test will probe.
- IMPORTANT: implement the error boundary so it can be toggled off via
  ?boundary=off — we need to demonstrate both the guarded and unguarded behaviour.

Verify by starting the server and confirming frames stream. Show me the output.
````

### Phase 2 — Q1 automation framework (target: 5h) — **the 15-point core**

````text
PHASE 2: Build q1_canvas_race/framework/ and tests/.

1) ws_chaos.py — WebSocket interception layer
   - Use Playwright's route_web_socket() to sit between page and server.
   - FibonacciJitter: delay_ms = 1000 * fib(step), step increments per intercepted
     frame, capped at 8000ms. Log every injected delay with seq + delay.
   - PayloadMutator: on a target seq, rewrite price to a corrupted mathematical
     state (1e+7, then 0.1+0.2 float artifact, then NaN) before forwarding.
   - Both must be composable and independently toggleable.

2) pixel_engine.py — the anti-AI core
   - Inject a JS coordinate calculation engine via page.evaluate that runs a
     requestAnimationFrame loop reading ctx.getImageData at computed grid coords.
   - Classify each sample: GRAY_LOADING (channel spread < 8 AND luminance in
     the 120-136 band) vs ACTIVE (channel spread > 40, hue bucketed to up/down).
   - Resolve a promise the instant a target cell crosses loading -> active,
     returning {cellId, x, y, rgb, performanceNowMs}.
   - Must survive canvas resize: derive grid coords from a calibration pass that
     scans for cell boundaries, never from hardcoded pixels.
   - Expose calibrate() to recompute the offset matrix on demand.

3) circuit_breaker.py
   - States: CLOSED -> OPEN -> HALF_OPEN. Failure classes: StaleFrameError,
     CoordinateDriftError, RepaintLagError.
   - On failure: call pixel_engine.calibrate() to recompute grid offsets, then retry
     with exponential backoff. After N consecutive failures, OPEN and cool down.
   - Emit a state-transition log line for every change. This is what we scroll on
     video to prove the resilience layer is real.

4) chained_actions.py
   - fire(page, target) executes hover -> mouse drag +15px on X -> click.
   - Must begin within 30-100ms of the pixel transition timestamp. Measure with
     time.perf_counter_ns(). Record actual latency.
   - If the window is missed, raise RaceWindowMissedError; do not silently pass.
     A missed window must be visible in the report as a real result.

5) tests/test_canvas_race.py
   - test_pixel_state_transition_detected_under_fibonacci_jitter
   - test_chained_actions_land_inside_race_window (asserts measured latency band)
   - test_circuit_breaker_recovers_from_coordinate_drift (force drift, assert recovery)
   - test_corrupted_scientific_notation_triggers_error_boundary (boundary=on -> ERR
     glyph appears in pixels)
   - test_corrupted_payload_silently_accepted_when_boundary_disabled (boundary=off ->
     assert we DETECT the silent corruption and fail loudly). This pair is the
     money shot: it proves the suite catches a real defect, not just green ticks.
   - Write per-test timing CSV + full-page screenshots to artifacts/.

Run the suite. Paste the real output including measured race-window latencies.
````

### Phase 3 — Q2 gateway + replay suite (target: 3h)

````text
PHASE 3: Build q2_crypto_replay/.

mock_gateway/server.js — Express on :8082:
- POST /v1/transactions -> 201, response HEADER `X-Transaction-Id: <uuid>`,
  body {challengeToken, serverTimestampMicros, salt}
- PUT /v1/transactions/:id -> requires headers:
    X-Frugal-Mac (hex), X-Frugal-Timestamp (micros), X-Frugal-Challenge
  Server recomputes HMAC-SHA512 over (rawBody + timestampMicros + salt) with the
  challenge-derived key and compares in constant time (crypto.timingSafeEqual).
- Nonce store: Map keyed on (mac + timestamp). Second sighting -> 409 Conflict with
  {error:"REPLAY_DETECTED"}. TTL sweep every 30s.
- Timestamp skew window: reject > 5s old with 422.
- config.js exports MODE = process.env.GATEWAY_MODE || 'SECURE'.
  In 'VULNERABLE' mode the nonce check is bypassed and replays return 200 OK.
  We need this to demonstrate the alerting path.

framework/hmac_signer.py — canonical body serialisation (sorted keys, no whitespace)
so client and server hash identical bytes. Document the canonicalisation choice; a
mismatch here is the classic real-world HMAC bug.

framework/chain_client.py:
- Step 1: POST, extract ID from the RESPONSE HEADER (not the body — the spec says
  header, and doing it right is a comprehension check).
- Step 2: parse challengeToken + serverTimestampMicros, generate a local microsecond
  timestamp, sign, PUT.
- Step 3: within 150ms of PUT completion, resend the byte-identical payload with the
  identical timestamp and MAC. Measure and log the actual replay gap in
  microseconds. If the gap exceeds 150ms, mark the run INVALID and retry rather
  than reporting a pass on an unmet precondition.

framework/vuln_reporter.py — on a duplicated 2xx, emit a CRITICAL structured log:
severity, CWE-294 reference, endpoint, both response codes, timing, and remediation.
Also write it to artifacts/VULNERABILITY_ALERT.json.

tests/test_replay_chain.py:
- test_secure_mode_rejects_replay_with_409
- test_tampered_body_rejects_with_401 (flip one byte, MAC must fail)
- test_stale_timestamp_rejected_422
- test_vulnerable_mode_emits_high_risk_alert (GATEWAY_MODE=VULNERABLE)

Run both modes. Paste output for each.
````

### Phase 4 — Q3 shadow DOM + CoT prompt (target: 2h)

````text
PHASE 4: Build q3_shadow_dom/.

demo/index.html — reproduce the assignment's exact structure:
<enterprise-portal id="root-gateway"> open shadow
  -> <payment-terminal class="obfuscated_v4_x89a"> CLOSED shadow
     -> <security-sandbox id="iframe-sandbox-wrapper"> open shadow
        -> <button class="trigger-finalize" data-qa-state="unlocked-token">
Class strings must regenerate randomly on every page load. Add proper ARIA:
role="button", aria-label, and an aria-live="assertive" status region that announces
the result. Include one real nested <iframe> too, since production sandboxes have one.

framework/closed_root_hook.js — injected via page.add_init_script BEFORE any page
script runs: monkey-patch Element.prototype.attachShadow to capture the returned
root (including mode:'closed') into a WeakMap + a global registry array, then call
through. Explain in the docstring why this is the only reliable way to reach a
sealed root from the automation layer, and why it is a test-harness affordance
rather than something to ship to production.

framework/deep_pierce.py — recursive traversal across open roots, registry-captured
closed roots, and same-origin iframes. Match on STABLE signals only: tag name,
role, aria-label, data-qa-state. Never on the obfuscated class.

framework/ax_tree_locator.py — resolve the same button purely from the accessibility
tree via CDP Accessibility.getFullAXTree, walking role/name/state and computing a
role-path like: application > region[payment] > button[name="Authorize Ledger Funds"].
Prove both routes land on the identical element.

tests/test_shadow_pierce.py — reload the page 10 times, assert the locator resolves
all 10 times despite class regeneration, and assert the class strings actually
differed between loads (otherwise the test is vacuous).

COT_SYSTEM_PROMPT.md — a dense expert-level Chain-of-Thought SYSTEM prompt that
trains an LLM to locate elements EXCLUSIVELY from the OS accessibility tree.
It must:
- Define the reasoning sequence: enumerate AX nodes -> filter by role -> disambiguate
  by accessible name + state -> verify uniqueness -> compute a role-path -> emit a
  stability confidence score with an abstain threshold.
- Explicitly FORBID: element IDs, absolute or structural XPath, visible text string
  matching, CSS selectors/classes, nth-child indexing, coordinates.
- Handle aria-live alert regions and role changes over time.
- Include 2 worked few-shot examples and 1 negative example showing correct refusal
  when the AX tree is ambiguous.
- Specify a strict output schema (JSON: role_path, confidence, abstain, rationale).
````

### Phase 5 — Section B (target: 8h) — **70 points, do NOT rush**

Ask for **one question at a time**. Blanket-generating 14 answers produces interchangeable AI prose, and the brief explicitly warns that your personal voice must be apparent.

````text
PHASE 5, question <N>: Draft an answer to Q<N>.
Constraints: hard maximum 150 words. Technical and specific — name the actual
mechanism, metric, header, isolation level, or algorithm. No filler openers ("In
today's fast-paced..."), no restating the question, no bulleted fluff.
Include at least one concrete number, threshold, or named tool.
End with the trade-off or the failure mode of your own proposal — showing you know
what your answer costs is what separates a senior answer from a generated one.
Give me 2 variants: one structural/architectural, one operational/diagnostic.
````

Then **you rewrite it in your own words.** Non-negotiable — they screen for plagiarism and voice.

#### Answer spines — the point each question is actually testing

- **Q4 (multi-agent drift):** the vulnerability is *shared epistemic ground truth*. Agent B derives the oracle from the same artifact Agent A mutated, so the test encodes the bug as the spec — an oracle problem, not a model-quality problem. Fix: a non-generative validation layer sourced from an independent, human-authored artifact (OpenAPI contract, TLA+/property-based invariants, golden datasets) that neither agent can write to. Mention write-permission separation.
- **Q5 (V8 heap):** socket buffer overflow on fd 12 → backpressure ignored → unresolved promises accumulate (68,240 closures retained) → each closure retains its stream chunk → old-space grows → GC compaction every 12ms at 98.4% heap = mark-compact thrash → allocation failure → abort. Key term: **retained closure graph via promise chain**. UI tests stay green because low concurrency never generates enough queue depth to hold retainers past a GC cycle.
- **Q6 (SQL injection):** f-string interpolation of `tenant_id` → `' OR '1'='1` escapes the tenant predicate; `filtering_date` is equally injectable and often unsanitised. Fix prompt: mandate parameterised queries only, forbid string concatenation in SQL, require an allow-list enum for column names, require the tenant scope to come from an authenticated session context rather than a caller argument, and specify an output schema the model must conform to.
- **Q7 (flaky test):** shared-core runners → CPU steal time and clock drift make a 15s sleep sometimes 4s of real work and sometimes 25s; `isVisible()` is a point-in-time poll with no retry, so it's a race, not a wait. Refactor: `expect(locator).to_be_visible()` web-first assertion, or a `MutationObserver`/`page.wait_for_function` on an explicit state attribute, plus event-driven waits on the network response that mutates the ledger.
- **Q8 (HikariPool):** profiling ladder — (1) pool telemetry, (2) thread dumps at 5s intervals looking for `BLOCKED` on JDBC vs `WAITING` on `getConnection`, (3) DB-side `pg_stat_activity` / `SHOW ENGINE INNODB STATUS` for lock waits, (4) correlate. Metrics: `hikaricp.connections.active/idle/pending`, `connections.acquire` p99, `connections.usage` p99, `connections.timeout` rate, thread states, and DB lock-wait time. Distinguisher: if `usage` time is high → slow queries/locks; if `acquire` is high while `usage` is low → pool undersized / thread-to-core misconfiguration.
- **Q9 (blank screen):** assertions ran against DOM presence, not paint. A CSS-in-JS throw halts layout construction but the nodes still exist in the DOM tree. Fix: visual regression on rendered pixels, `element.checkVisibility()`, Layout Instability / LCP / CLS from the Performance API, non-zero `getBoundingClientRect`, `console`+`pageerror` listeners promoted to hard failures, and a synthetic "first meaningful paint has non-background pixels" gate.
- **Q10 (agentic runaway):** external control plane — ephemeral sandbox with no direct push rights, all writes go through a PR-proposal API with a per-hour budget, token/compute quota with a hard kill, branch-creation rate limit, and a required human approval on any diff touching protected paths. Telemetry to flag hallucination loops: semantic similarity of consecutive diffs above threshold, non-decreasing test-failure count across N iterations, branch-creation velocity, repeated identical error signatures, cumulative token spend per task, and diff-churn ratio (lines rewritten / lines net changed).
- **Q11 (AST test selection):** parse AST diffs → resolve changed symbols → walk a call/import graph to build a reverse dependency closure → map to tests via a coverage-derived symbol→test index. Guard against under-selection: always run tests touching contract boundaries, keep a permanent "critical path" always-on set, run the full suite nightly, and track escaped-defect rate per selection to tune the closure depth.
- **Q12 (self-healing):** the engine scored *visual/structural* similarity without weighting *semantic destructiveness*. `.btn-danger` proximity is not identity. Fix: composite score = Levenshtein on locator string (weight w1) + DOM graph edit distance over the neighbour subgraph (w2) + accessible-name similarity (w3) + role match (w4), with a destructive-action classifier that forces a hard abstain — never auto-heal a candidate whose accessible name contains delete/wipe/drop/confirm semantics. Below-threshold → quarantine and fail, never click.
- **Q13 (MCP sandbox):** replace the free-form `command` string with a fixed-verb schema: `{"operation": {"enum": ["tail_log"]}, "filename": {"pattern": "^[a-zA-Z0-9_.-]+\\.log$"}, "lines": {"type": "integer", "maximum": 150}}`, `additionalProperties: false`. No shell at all — execve the binary directly with an argv array, path-resolve and assert the realpath stays under the allowed subdirectory (blocks `../` traversal), read-only mount, no network, dropped privileges, timeout, output size cap.
- **Q14 (log ingestion):** edge accepts and immediately returns 202 after writing raw payloads to object storage; only a pointer goes onto the broker (Kafka/SQS) — never base64 screenshots in the message body. Partition by tenant, autoscaled consumer pool, dead-letter queue. Protect downstream: token-bucket rate limiter with a shared quota accountant, request coalescing/dedupe by stack-trace hash (identical failures collapse to one LLM call), tiered triage where regex/heuristics handle known signatures and only novel ones reach the model, and a bounded connection pool with backpressure to the consumers rather than unbounded DB fan-out.
- **Q15 (tracing):** root cause is **LedgerDB row-lock contention** in span 5 (2043ms of the 2150ms) — the gateway 500 is a symptom. Correlation: W3C `traceparent` header propagated across process boundaries, parent/child span IDs reassembling the tree in the collector. Triage sheet: check current isolation level (likely REPEATABLE READ / SERIALIZABLE causing gap locks on the `WHERE id = 92` hot row), recommend READ COMMITTED where semantics allow, shorten transaction scope, consistent lock ordering to prevent deadlock cycles, `innodb_lock_wait_timeout` tuning, and an index check so the update takes a row lock rather than escalating.
- **Q16 (prompt critique):** the flaw is iterative patching — each turn appends contradictory constraints while the model anchors on its first wrong answer; the context fills with dead regex attempts, and requirements arrive only after failure. Restructure: one system prompt stating the full input grammar up front (ISO 8601 prefix, multiline, nested arrays), 3 few-shot input/output pairs including a negative case, an explicit reasoning order, a demand for a named-group flavour-specified pattern (state PCRE vs RE2 — recursion is unavailable in RE2), and the honest recommendation that a bracket-counting parser beats regex for arbitrary nesting.
- **Q17 (HIPAA test strategy):** rough split — Unit 25%, AppSec 20%, Contract 15%, API Functional 20%, Visual Regression 5%, Load 15%, tied to blast radius. Then give each tier exactly one non-overlapping job: unit = algorithmic correctness of transforms; AppSec = PHI exposure, authz boundaries, encryption at rest/in transit, audit-log completeness; contract = producer/consumer schema drift between device firmware and ingest; API functional = business-rule and state-machine correctness; visual = clinician-facing rendering of critical values; load = durability and ordering guarantees under concurrency spikes (no dropped or reordered vitals).
- **Q18 (OpenAPI mutation):** boundaries — tenantId 999, 1000, 999999, 1000000, 0, -1, 2^31, 2^63, "1000", 1000.0, null; transactionAmount 0.00, 0.01, 50000.01, -0.01, 1e+308, NaN, Infinity, 0.1+0.2 precision drift; accountPasscode 3/4/8/9 chars, lowercase, unicode homoglyphs, `\n` anchor bypass (the `^...$` pattern in a multiline-permissive engine); `X-Idempotency-Key` non-UUID, duplicate, omitted; `targetRegion` outside enum, duplicated query param (pollution — first/last-wins divergence). **The star answer: `NestedMetaTag` is self-referential with no depth cap — send 10,000 levels of nesting to blow the parser stack.** Assertions: strict type checking with no coercion, explicit recursion depth limit, request body size cap, duplicate-parameter rejection, `additionalProperties:false` enforced at runtime not just in spec, and a guarantee of 4xx (never 5xx) for every malformed input.
- **Q19 (sign-off gate):** rules engine ingesting weighted signals → hard gates (any critical CVE, any P1 open bug, coverage delta negative on changed lines) that veto regardless of score, plus soft weighted scoring for the rest. Emphasise **coverage on changed lines**, not global percentage, and flake-adjusted pass history so a known-flaky test doesn't block. Auto-rollback trigger on post-deploy SLO burn rate.
- **Q20 (closed-loop observability):** tag tests and production traces with a shared feature/route identifier so APM data can rank test priority by real traffic and real error density. System: production metrics → prioritisation service → test selection weights + load-profile generator that replays production traffic shapes → chaos injection scheduled against the top-N hottest service channels, gated by error budget so you never inject during an active incident.

**Behavioural profiles (A–D):** they're screening for AI-native but disciplined. Defensible set: **A-ii** (stabilise the release, refactor after — with the caveat that you file the debt ticket), **B-i** (enforce conventions on the agent), **C-ii** (prototype to discover requirements in ambiguity), **D-i** (challenge the vanity metric). Answer honestly though — consistency with your Section B answers matters more than guessing their key.

### Phase 6 — Q21 article (target: 3h)

Pick **Topic B (MCP sandboxes)** or **Topic D (self-healing algorithms)** — both let you reuse work you've already done in Q13/Q12, so the article carries real implementation weight instead of survey prose. Topic B is the stronger differentiator for an "AI-Native" role.

````text
PHASE 6: Draft Q21 on Topic B — "Securing the AI Workspace: Designing Restrictive
MCP Sandboxes to Prevent Arbitrary Code Execution by Autonomous Developer Agents."
900-1200 words, Markdown, H2/H3 structure, at least 2 real code blocks (the
before/after JSON schema from Q13 and the argv-exec wrapper).
Required content: the threat model (prompt injection as a privilege-escalation
vector, confused deputy), why string-based tool schemas are the core flaw, the
capability-based alternative, defence in depth (schema -> argv exec -> path realpath
containment -> filesystem/network isolation -> resource caps -> audit log), and an
explicit TRADE-OFFS section covering what you lose: agent capability ceiling,
schema maintenance burden, and the false sense of safety from allow-lists.
Cite sources properly with links. No uncredited material.
Voice: engineer writing from implementation experience, first person where natural.
Avoid: "In today's rapidly evolving landscape", "delve", "robust", "leverage" as a
verb, tricolon summary sentences.
````

Then rewrite the intro and conclusion yourself in full — those are the paragraphs a human reviewer reads most closely.

---

## 4. Video recording protocol

Three checkpoints per folder, or you're auto-filtered. Record **after** everything works.

**Per-question video (~4–6 min each), single continuous take:**

1. **Output window (~90s)** — terminal, run the suite live. Show passing tests *and* the deliberate failure case (corrupted payload caught / vulnerability alert fired). Show the artifacts folder afterwards.
2. **Source code (~2–3 min)** — IDE, scroll the full directory tree, then open each module and narrate *why*, not *what*. "This circuit breaker recalibrates grid offsets instead of retrying blindly, because a stale coordinate will fail identically forever."
3. **GenAI prompt history (~90s)** — Antigravity chat / `PROMPTS.md`. Show a prompt that **failed** and how you diagnosed and corrected it. That single moment is the strongest signal you're steering the AI rather than the reverse.

Recording tips: 1080p minimum, IDE font bumped to ~16pt so code is legible on a reviewer's laptop, mic test first, close notifications. Name files `Q1_Workflow_NandanPerumalla.mp4`.

**Video CV (Q23, exactly 2–3 min)** — roughly 30s per prompt, scripted but not read aloud stiffly:
- Q1 → the AI-native engineer's job has moved from producing code to **specifying, constraining, and verifying** it; the scarce skill is designing the oracle.
- Q2 → use *this* assignment: undocumented canvas state with no DOM contract, solved by building a pixel-level state machine.
- Q3 → your actual practice: pinned deps, review every generated diff, never paste secrets, parameterised queries enforced by prompt contract, and independent verification of AI-written tests.
- Q4 → first principles: reproduce, bisect, instrument, form a falsifiable hypothesis, and read the source/spec. Ground it in a specific past debug.

---

## 5. 32-hour timeline

| Block | Hours | Work |
|---|---|---|
| 1 | 0–2 | Repo scaffold, deps pinned, Master Prompt loaded, Q1 testbed running |
| 2 | 2–7 | Q1 framework + tests green, artifacts generating |
| 3 | 7–10 | Q2 gateway + replay suite, both modes |
| 4 | 10–12 | Q3 pierce + CoT prompt |
| 5 | 12–14 | **Sleep / break** — protect this, the Section B answers need a clear head |
| 6 | 14–22 | Section B Q4–Q20, one at a time, rewritten in your voice |
| 7 | 22–25 | Q21 article |
| 8 | 25–28 | Record 3 workflow videos + video CV |
| 9 | 28–30 | Drive upload, permissions, Q22 links + social screenshots |
| 10 | 30–32 | Assemble PDF, compliance pass, buffer |

---

## 6. Submission compliance checklist

Structural non-compliance is auto-filtered before a human reads a word. Verify every line.

- [ ] Single unified PDF, named `Nandan_Perumalla_SRM_University_AP_<RollNumber>.pdf`
- [ ] Section 0 answered — all 6 items, including explicit bond consent and stipend/CTC confirmation
- [ ] Section A heading with Q1/Q2/Q3 laid out **exactly** as the template shows
- [ ] Three separate Drive folder links (one per question — not one shared folder)
- [ ] Every link set to "Anyone with the link can view" — **test each in an incognito window**
- [ ] Each folder contains raw source code + one single combined workflow video
- [ ] Every video shows all three checkpoints: output, source, prompt history
- [ ] Section B: Q4–Q20 answered in-doc, each ≤150 words (run a word count on every one)
- [ ] Behavioural profiles A–D: one choice each, recorded in the doc
- [ ] Q19 answered (zero marks but compulsory)
- [ ] Q21 article in-doc, 750–1500 words, Markdown formatting preserved in the PDF
- [ ] Q22: full name, LinkedIn, resume PDF link, GitHub/LeetCode, live project links
- [ ] Q22 social task: followed + engaged on all 5 channels, screenshots embedded
- [ ] Q23 video CV link at the very end, 2–3 min, permissions cleared
- [ ] Delivered to the placement cell officer before the 32-hour close

---

## 7. Guardrails when the agent goes off the rails

- **It writes `time.sleep()` anywhere in test logic** → reject, restate constraint 2, ask for a state-driven wait.
- **It hallucinates a Playwright method** → make it print `dir()` on the object or check the installed version first.
- **It claims exact-150ms timing without measuring** → demand `perf_counter_ns` instrumentation and a logged actual value.
- **It hardcodes canvas pixel coordinates** → reject; coordinates must come from the calibration pass, that's the entire point of Q1.
- **It writes Section B answers over 150 words or in generic voice** → regenerate with the constraint, then rewrite yourself.
- **It gets stuck looping on one bug** → stop, read the actual error yourself, and give it a narrower prompt with the specific traceback. Then log that exchange in `PROMPTS.md` — it's exactly the material the video needs.
