> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 2. Quality attributes

### 2.1 Cost

| Item | Target |
|---|---|
| Infra at idle | about $0 (free grants; cluster stopped; LB Service deleted so the public IP is released) |
| AKS node | about $1-3/month (ARM64 `B2pls_v2`, about $0.03/h, 20-80 h/month) |
| LLM calls | about $5-12/month (Anthropic default, OpenAI fallback) |
| Azure Managed Redis B0 | about $13/month while the estate is up (accepted 2026-10-28) |
| After the 12-month grant (05/2027) | Postgres and ACR start billing; about $20-35/month |

Detail: [13](13-cost.md).

### 2.2 Latency and cold start

- Cold run: 3-7 min for `az aks start`, node and image pull, plus 1-3 min for the LB public IP.
  `SENTINEL_KEEP_WARM=true` pays this once per demo session.
- Pipeline run timeout: 600 s (configurable). `mttr_seconds` is measured from webhook receipt, so it
  excludes the cold start.
- Datadog runtime synthetics run every 30 min with one retry a minute later, so a runtime scenario
  alerts within about 30 min ("Run test now" to demo faster).
- AKS stop and start take 5-10 min each way; Postgres auto-restarts after 7 days of pause.

### 2.3 Agent caps (enforced in code)

| Cap | Value |
|---|---|
| Tool calls per incident | 20, counted across every run including fallback re-runs; exhaustion escalates |
| Reflexion loops | at most 2, triggered when confidence < 0.7 |
| Reverification FAIL retry | at most 1 |
| Decision gate | confidence >= 0.7 and the root cause is a specific deploy, else escalate |
| Resume after restart | at most once; caps and the wall-clock deadline are absolute from the first start |
| Token budget alert | 50K tokens per incident, logged as `incident_token_budget_exceeded` |

### 2.4 Reliability

- One replica; incidents are independent `asyncio.Task`s with their own short-term memory and trace.
- Webhook dedupe on `correlation_id` (24 h in-memory TTL plus the DB); body-size cap (413),
  concurrency cap (429), 503 while shutting down.
- Worst-case shutdown 37 s (drain 20 + 2 + trace flush 5 + pool close 10);
  `terminationGracePeriodSeconds: 45`.
- One concurrency group `sentinel-backend` serialises every backend-using workflow; GitHub keeps
  only one pending run, so a third simultaneous alert cancels the waiting one (accepted at demo cadence).
- Nightly 02:00 UTC scale-down: a forgotten keep-warm session costs at most one night.

### 2.5 Evaluation targets

Each scenario run is scored on four ground-truth checks (fired, classified `signal_type`,
correlated culprit, revert-PR target), each 0 or 1, plus judge dimensions on a 0-1 scale.
Runs whose models include the judge model are `judge_conflict` and never counted. Detail: [12](12-evaluation.md).

### 2.6 Delivery quality

- One phase = one branch + one PR; one task = one commit with unit and integration tests.
- Green means `VERDICT GREEN` from a full run of the quality gate; `PARTIAL` and `INCONCLUSIVE` are not green.
- Backend boots (`poetry run sentinel serve`) after any dependency or module-level change.
