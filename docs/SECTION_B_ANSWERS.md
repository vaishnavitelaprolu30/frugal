# Section 0 Declarations & Section B Technical Answers

**Candidate:** Nandan Perumalla · **Role:** AI-Native SWE Intern · **Company:** Frugal Testing / BuildNexTech

---

## Section 0: Mandatory Declarations

1. **Full Legal Name:** Nandan Perumalla
2. **University & Graduation Year:** SRM University AP — Batch of 2027
3. **Contact Email & Phone:** nandan.perumalla@frugaltesting.com · +91-9876543210
4. **Bond Consent:** I explicitly confirm consent to the 36-month service bond (inclusive of 12-month internship).
5. **Stipend & CTC Acknowledgment:** Confirmed ₹25,000/month internship stipend and ₹8.5 LPA base CTC upon conversion.
6. **Self-Declaration:** All automated testbeds, frameworks, prompt logs, and answers were authored specifically for this submission.

---

## Section B: Technical Scenario Responses (Q4–Q20)

### Q4: Multi-Agent Ground Truth Drift under Autonomous Mutation

**Root Cause & Mechanism:**
Agent B derives its test oracle from the identical mutated artifact produced by Agent A. This shared epistemic drift transforms the test suite into an echo chamber where mutated bugs are encoded as specification.

**Proposed Solution:**
Decouple oracle generation by establishing a non-generative validation layer sourced strictly from human-authored invariants (OpenAPI schemas, TLA+ specifications, or golden datasets stored in read-only storage with `0444` permissions). Implement a cryptographic verification hook (`sha256` integrity check) that blocks Agent B from reading any artifact modified within the current execution pipeline.

**Metrics & Thresholds:**
Enforce zero diff allowance on contract invariants (`diff_count == 0`) and cap automated PR mutation velocity at 5 changes/hour.

**Trade-Off & Failure Mode:**
Restricting agents to static contracts increases manual schema maintenance overhead and causes agent execution to fail when genuine upstream contract changes occur.

---

### Q5: Node.js V8 Heap Exhaustion under Unhandled Backpressure

**Root Cause & Mechanism:**
Socket buffer overflow on file descriptor 12 creates ignored backpressure. Unresolved promise closures accumulate (68,240 retained instances), retaining incoming stream chunks in V8 old-space heap. GC compaction triggers every 12ms at 98.4% heap limit, causing mark-compact thrash and allocation failure aborts. Low-concurrency UI tests pass because stream queues drain before GC boundaries.

**Proposed Solution:**
Implement stream backpressure handling using `stream.pipeline()` with highWaterMark capped at 16KB. Instrument `process.memoryUsage().heapUsed` threshold monitoring at 80% to emit `SIGUSR2` heap dumps and pause consumer sockets (`socket.pause()`).

**Metrics & Thresholds:**
Cap old-space memory allocation at 1024MB (`--max-old-space-size=1024`) and enforce p99 garbage collection pause times < 15ms.

**Trade-Off & Failure Mode:**
Pausing sockets drops instantaneous ingress throughput by ~35% under peak traffic spikes.

---

### Q6: Parameter Injection & Tenant Isolation Bypass in Dynamic SQL Prompting

**Root Cause & Mechanism:**
F-string interpolation of `tenant_id` (`f"WHERE tenant = '{tenant_id}'"`) allows `' OR '1'='1` payload injection, escaping tenant predicate boundaries and exposing cross-tenant data.

**Proposed Solution:**
Enforce parameterised queries exclusively (`SELECT * FROM ledger WHERE tenant = $1`) via database adapter drivers (PostgreSQL `pg-promise` / Python `asyncpg`). Enforce dynamic prompt contract requiring an AST validator (`sqlglot`) to verify string concatenation is absent prior to query execution. Extract tenant context from authenticated JWT session objects rather than untrusted request parameters.

**Metrics & Thresholds:**
AST parameter check validation time < 2ms; zero string format patterns permitted (`regex: f".*SELECT.*%s.*"`).

**Trade-Off & Failure Mode:**
AST validation adds ~2ms execution overhead per query and rejects complex dynamic subqueries requiring raw SQL building.

---

### Q7: Flaky Assertion Failures in Shared CI Environments

**Root Cause & Mechanism:**
Shared-core CI runners exhibit CPU steal time (>25%) and clock drift, expanding a 15s static sleep into varied execution intervals. Point-in-time DOM polling (`isVisible()`) evaluates before asynchronous network hydration completes, triggering race condition failures.

**Proposed Solution:**
Replace point-in-time polling with web-first auto-retrying assertions (`expect(locator).to_be_visible()`) anchored to explicit state attributes (`data-state="hydrated"`). Intercept underlying API network responses via `page.wait_for_response()` to synchronize test execution directly with network event completion rather than arbitrary timers.

**Metrics & Thresholds:**
Set polling interval to 50ms with a hard 5000ms timeout ceiling; CI runner CPU steal threshold < 10%.

**Trade-Off & Failure Mode:**
Network-anchored waits fail if backend WebSocket streams fail to emit explicit completion events.

---

### Q8: HikariCP Connection Pool Exhaustion Diagnostic Ladder

**Diagnostic Ladder & Profiling Steps:**
1. Collect HikariCP telemetry metrics (`hikaricp.connections.active`, `.idle`, `.pending`).
2. Capture JVM thread dumps at 5-second intervals via `jstack`, searching for `BLOCKED` states on JDBC socket reads vs `WAITING` on `getConnection()`.
3. Query database engine lock status (`pg_stat_activity` / `SHOW ENGINE INNODB STATUS`) for transaction lock waits.
4. Correlate thread execution IDs with database transaction PIDs.

**Metrics & Decision Boundary:**
High `connections.usage` time with low `pending` count indicates slow queries or row-lock contention. High `connections.acquire` time (>1000ms) with elevated `pending` counts indicates pool undersizing or thread starvation.

**Trade-Off & Failure Mode:**
Increasing connection pool size escalates memory pressure and risks context-switching overhead on database CPU cores.

---

### Q9: Visual Regression False-Positives on CSS-in-JS Blank Paints

**Root Cause & Mechanism:**
Standard DOM assertions evaluate node presence in the DOM tree, ignoring paint failures. CSS-in-JS compilation exceptions halt layout construction while DOM nodes remain present, causing tests to pass against un-rendered blank screens.

**Proposed Solution:**
Implement visual regression pixel sampling coupled with `element.checkVisibility()` and Layout Instability metrics from the Performance API. Inspect `getBoundingClientRect()` for non-zero dimensions and capture browser `console` / `pageerror` events, promoting uncaught CSS-in-JS runtime exceptions to immediate test failures.

**Metrics & Thresholds:**
Enforce Cumulative Layout Shift (CLS) < 0.1, LCP < 2.5s, and non-zero render dimensions (`width > 0 && height > 0`).

**Trade-Off & Failure Mode:**
Visual canvas sampling increases test duration by ~120ms per screen state capture.

---

### Q10: Agentic Execution Runaway & Budget Containment Control Plane

**Control Plane Architecture:**
Deploy an external sandbox control plane restricting autonomous developer agents to ephemeral environments. Require all writes to pass through a PR proposal API with strict rate limits. Enforce hard token and compute budget limits with an automated kill-switch listener (`SIGKILL` on budget breach).

**Hallucination Loop Telemetry Metrics:**
1. Semantic similarity of consecutive code diffs > 0.88 across 3 iterations.
2. Non-decreasing test failure count across 4 consecutive execution cycles.
3. Branch creation velocity exceeding 10 branches/hour.
4. Cumulative task token spend exceeding 150,000 tokens.

**Trade-Off & Failure Mode:**
Aggressive token caps interrupt complex refactoring tasks mid-execution, requiring human intervention to re-grant budget.

---

### Q11: AST-Based Predictive Test Selection Engine

**Selection Engine Protocol:**
Parse Git diffs into Abstract Syntax Trees (AST) using `babel/parser` or Python `ast`. Identify mutated functions, classes, and exported symbols. Walk call graph dependency trees to generate a reverse dependency closure, mapping mutated symbols to corresponding test files via a coverage-indexed symbol matrix.

**Guardrails Against Under-Selection:**
1. Permanently pin critical path authentication and payment tests to an always-on test set.
2. Execute full test suite on nightly schedules.
3. Track escaped defect metrics per selection cycle, dynamically expanding call graph closure depth (depth 2 -> 3) if missed coverage is detected.

**Trade-Off & Failure Mode:**
AST analysis fails to capture dynamic reflection or runtime string-based dependency injection calls.

---

### Q12: Destructive Action Safeguards in Self-Healing Locators

**Root Cause & Safeguard Architecture:**
Visual and structural similarity algorithms lack semantic intent awareness. Proximity scoring algorithm target `.btn-danger` proximity over action safety.

**Proposed Solution:**
Implement composite locator scoring:
`Score = w1 * StringLevenshtein + w2 * GraphEditDistance + w3 * AccessibleNameSim + w4 * RoleMatch`.
Integrate a Destructive Action Classifier: parse candidate node accessible names for destructive semantics (`delete`, `drop`, `wipe`, `purge`, `confirm`). If a candidate contains destructive keywords, force a hard abstain (`score = 0`), quarantining the test instead of auto-healing.

**Metrics & Thresholds:**
Abstain threshold < 0.82; 100% hard block on destructive semantic matches.

**Trade-Off & Failure Mode:**
Requires manual engineer triage whenever UI redesigns modify button accessible names.

---

### Q13: Restrictive MCP Sandbox Schema for File Inspection

**Insecure Free-Form Schema:**
`{"command": "string"}` allows injection payload execution (`tail /var/log/app.log; rm -rf /`).

**Secure Strict Schema:**
```json
{
  "operation": { "type": "string", "enum": ["tail_log"] },
  "filename": { "type": "string", "pattern": "^[a-zA-Z0-9_.-]+\\.log$" },
  "lines": { "type": "integer", "maximum": 150 }
}
```

**Sandbox Execution Containment:**
Execute binary directly via `execve('/usr/bin/tail', ['-n', lines, resolved_path])` without spawning shell shells (`sh -c`). Verify `fs.realpathSync()` path remains within `/var/log/app/` subdirectory (preventing `../` directory traversal). Run inside read-only docker container with dropped Linux capabilities (`CAP_DROP_ALL`).

**Trade-Off & Failure Mode:**
Rigid schemas prevent agents from running custom log analysis flags or piping output to grep.

---

### Q14: Scalable Async Log & Screenshot Ingestion Pipeline

**Edge Ingestion Pipeline:**
Edge API gateway receives test execution payloads, immediately writes raw binary assets (screenshots, traces) to S3/GCS object storage, and emits lightweight metadata pointers to Kafka/SQS brokers before returning HTTP 202 Accepted.

**Downstream LLM Protection Mechanisms:**
1. Deduplicate stack traces using MD5 error hashes, collapsing identical failure bursts into single LLM triage requests.
2. Rate-limit model queries via Token Bucket algorithm (max 50 requests/min).
3. Tiered Triage Engine: Regex patterns process known errors locally; only novel unclassified failures hit LLM APIs.

**Metrics & Thresholds:**
Ingestion edge latency < 45ms; LLM triage queue depth ceiling of 500 messages.

**Trade-Off & Failure Mode:**
Deduplication hides transient timing variations occurring across distinct parallel test nodes.

---

### Q15: Distributed Trace Triage of Database Row-Lock Contention

**Root Cause Identification:**
Distributed trace inspection reveals Span 5 (`LedgerDB.executeUpdate`) consumes 2043ms out of 2150ms total request duration. The Gateway 500 status is a symptom of transaction timeout caused by row-lock contention on hot record `WHERE id = 92`.

**Correlation Mechanism:**
Trace propagation using W3C `traceparent` headers (`00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01`) carried across service boundaries reassembles parent/child span timing trees.

**Triage & Remediation Sheet:**
1. Inspect database transaction isolation levels (convert `SERIALIZABLE` to `READ COMMITTED` where semantics permit).
2. Enforce explicit lock ordering across application services to eliminate deadlock cycles.
3. Optimize table indexing to convert table-scan locks to targeted single-row index locks.

**Trade-Off & Failure Mode:**
Relaxing isolation levels increases risk of non-repeatable read anomalies under concurrent transactions.

---

### Q16: Structured Prompt Reconstruction for Log Parsing

**Prompt Flaw Analysis:**
Iterative conversational prompting appends contradictory instructions, causing model output drift and context window bloat filled with failed regex attempts.

**Reconstructed System Prompt:**
```text
SYSTEM: You are a deterministic log parser. Parse multiline application logs into JSON conforming strictly to schema: {timestamp: ISO8601, log_level: STR, component: STR, trace_id: STR, message: STR}.
Rules:
1. Extract timestamp matching ^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z.
2. Group stack traces into single message string.
3. Emit output strictly as JSON. No conversational text.
```

**Few-Shot Input/Output Pair:**
*Input:* `2026-08-12T08:00:00.123Z [ERROR] auth-service (trace_992): Invalid token`
*Output:* `{"timestamp": "2026-08-12T08:00:00.123Z", "log_level": "ERROR", "component": "auth-service", "trace_id": "trace_992", "message": "Invalid token"}`

**Recommendation:**
Use dedicated AST string parsers over regex for deeply nested log payloads.

---

### Q17: Healthcare HIPAA Test Strategy & Risk Allocation

**Test Suite Allocation Matrix:**
- Unit Tests: 25% (Algorithmic data transforms & validation logic)
- AppSec & Compliance: 20% (PHI redaction, authz boundaries, audit logs)
- Contract Tests: 15% (Device firmware API schema drift)
- API Functional: 20% (Business logic & state machines)
- Visual Regression: 5% (Clinician dashboard rendering)
- Load & Stress: 15% (High-concurrency vital stream ingestion)

**Non-Overlapping Scope Directives:**
- *Unit:* Test data anonymization functions offline with mock synthetic data.
- *AppSec:* Verify HIPAA compliance invariants (zero unencrypted PHI in logs/S3, 100% audit record capture on access).
- *Contract:* Assert schema compatibility between medical hardware data producers and backend APIs.

**Trade-Off & Failure Mode:**
Rigid AppSec verification increases deployment pipeline duration by ~4 minutes per release.

---

### Q18: OpenAPI Payload Boundary Mutation Strategy

**Boundary Mutation Vectors (`/v1/payments` endpoint):**
1. `tenantId`: `0`, `-1`, `9999999999999999999`, `"1000"`, `null`, `""`, `' OR '1'='1`
2. `transactionAmount`: `0.00`, `-0.01`, `0.0000001`, `1e+308`, `NaN`, `Infinity`
3. `accountPasscode`: `""`, `"a"` (under 4 chars), `"a"*10000`, `\n` newline bypass payloads
4. `NestedMetaTag`: 10,000 recursively nested JSON tags (Parser Stack Overflow Attack)

**Expected Assertions:**
Gateway MUST reject all mutated payloads with HTTP `4xx` (Client Error, never `5xx` Server Error), enforcing strict schema bounds (`additionalProperties: false`) and depth caps (max depth 10).

**Trade-Off & Failure Mode:**
Deep mutation testing expands API fuzzing suite execution time by ~15 minutes.

---

### Q19: Autonomous Deployment Sign-Off Rules Engine

**Sign-Off Rules Engine Criteria:**
- **Hard Gate 1:** Zero Critical/High CVEs in dependency vulnerability scans (`trivy`).
- **Hard Gate 2:** 100% pass rate on critical path E2E regression tests.
- **Hard Gate 3:** Code coverage delta on modified lines ≥ 90% (ignoring global suite percentage).
- **Soft Metric:** Historical test flakiness score < 2%.

**Automated Rollback Trigger:**
If post-deploy APM metrics show HTTP 5xx error rate > 1.5% or p99 latency degrades by > 25% over a 5-minute window, trigger instant automated canary rollback.

**Trade-Off & Failure Mode:**
Strict line coverage gates block urgent emergency hotfixes containing low-coverage configuration updates.

---

### Q20: Closed-Loop Production Observability Test Prioritization

**Closed-Loop Architecture:**
Ingest production APM telemetry (Prometheus / Datadog spans) into a Test Prioritization Engine. Rank test suite execution order dynamically based on real-world traffic volume, failure rates, and hot service routes.

**Production-Replay Chaos System:**
Generate synthetic load profiles mimicking real traffic shapes. Inject network latency chaos (`150ms - 500ms`) against the top 10% most heavily trafficked microservice endpoints during staging integration runs.

**Safety Barrier:**
Gate chaos injection by production error budget: auto-disable chaos testing whenever production error budget burn rate exceeds 0.5%/hr.

**Trade-Off & Failure Mode:**
Prioritizing hot paths risks under-testing cold edge-case features, allowing latent bugs to build in low-volume modules.

---

## Behavioural Profile Choices

- **Profile A (Shipping vs Quality under Deadline):** **Choice A-ii** (Stabilize critical paths for release, document technical debt, refactor immediately post-release).
- **Profile B (Agent Guidance & Code Standards):** **Choice B-i** (Enforce strict prompt constraints and AST linting rules directly on agent execution).
- **Profile C (Ambiguous Requirements):** **Choice C-ii** (Build rapid working prototypes to discover implicit constraints and iterate with stakeholders).
- **Profile D (Engineering Metrics):** **Choice D-i** (Challenge vanity metrics like global code coverage, refocusing team on changed-line coverage and defect escape rate).
