## 9. Observability

### 9.1 Traces
- OpenTelemetry end to end: Kong `opentelemetry` (`traceparent`) to `chat-api` (FastAPI, asyncpg / SQLAlchemy, Voyage and Anthropic HTTP calls) to workers (`traceparent` carried in Kafka headers) to Cloud Trace (free to 2.5M spans/month). SQL parameter capture off; no request bodies in spans (D13o).
- Span names: `chat.turn`, `auth.verify`, `principal.load`, `guard.input`, `guard.model_armor`, `embed.query`, `retrieval.hybrid_sql`, `retrieval.rerank`, `retrieval.gate`, `llm.stream`, `guard.output`, `persist.turn`, `outbox.relay`, `consumer.<role>`.
- Langfuse Cloud (Python SDK 5.x, behind one wrapper; the v2 `trace()/span()/generation()` calls are gone, G-15): one trace per turn with generations (model, usage, cache read), retrieval span (chunk ids, scores), gate result. `@observe` with `capture_input=False` / `capture_output=False` on sensitive spans and `mask_otel_spans` for export masking (the legacy `mask=` does not cover OTel spans); input is scrubbed text only; tagged by `tenant_id`; never blocks the request path.

### 9.2 Metrics (log-based and OTel, in Cloud Monitoring)

| Metric | Meaning |
|---|---|
| `chat_ttft_ms`, `chat_total_ms` | TTFT and full answer latency (SLO inputs) |
| `retrieval_first_stage_ms`, `rerank_ms` | embed + SQL, rerank latency |
| `rerank_fallback_total{reason}`, `rerank_429_total`, `retrieval_degraded_ratio` | rerank fallbacks, rate limits and the share of degraded turns |
| `gate_refusals_total` | confidence gate refusals |
| `guard_blocks_total{guard}` | Model Armor, input cap, citation verifier, PII blocks |
| `llm_fallback_total`, `llm_breaker_state` | fallback and breaker |
| `answer_cache_hit_ratio` | cache effectiveness |
| `outbox_oldest_age_s`, `consumer_lag{group}` | event pipeline health |
| `acl_apply_lag_s` | time from `acl_change_requests.requested_at` to `applied_at` |
| `dlq_messages_total` | poison messages |
| `tenant_budget_rejections_total{tenant}` | per-tenant limits |
| `default_partition_rows` | rows in the DEFAULT `chunks` / `messages` partitions (bug signal) |
| `db_connections_in_use` | against the 300-connection pool budget |
| `llm_cost_usd_total{provider,model}` | LLM spend from token counts and a price table in config; the budget alert uses GCP billing plus this metric (ADR-025 R73) |
| `readiness_failing` | 1 while `/readyz` fails (ADR-025 R74) |
| `model_retirement_days` (gauge) | days until the nearest retirement date of a configured model (ADR-025 R6, R74) |
| `citation_rejected_total` | unverified `[n]` markers stripped by the citation verifier (ADR-025 R46) |
| `outbox_unpublished` (OTel gauge) | outbox rows with `published_at IS NULL`; emitted by E5, moved to the metrics registry by E9-T5 (ADR-025 R55, R71) |
| Kong `prometheus` series | scraped locally; exported to Cloud Monitoring via OTel in the cloud |

### 9.3 Logs
Structured JSON to stdout, redacted before writing: `ts`, `severity`, `trace`, `request_id`, `tenant_id`, `advisor_hash`, `event`, `error_code`. No request bodies, queries, prompts, tool payloads or exception text for clients. Kong's `file-log` audit goes to Cloud Logging and a log sink exports it to BigQuery `gateway_audit`. Logging costs $0.50/GiB after 50 GiB per project (evidence-r2.md).

### 9.4 Health
`/healthz` (liveness) and `/readyz` (DB role flags, FORCE RLS, partition grants, pgvector >= 0.8, Kafka reachability (degraded for chat), model availability, verifier initialised) as in §6.1. Kong status listener for the gateway. `demo-prewarm` calls `/readyz` from inside the VPC.

### 9.5 SLOs and alerts

| SLO | Target | Applies to |
|---|---|---|
| Availability (one SLO, with burn-rate alert) | 99.5% monthly of chat requests not failing | `prod` profile only |
| Latency | TTFT p95 < 3.5 s (p50 < 2.0 s), full answer p95 < 8 s | `demo` and `prod` (measured; estimates) |
| Retrieval | first stage p95 < 300 ms, rerank p95 < 700 ms | both |

Alert thresholds (ADR-025 R72): outbox oldest age > 300 s; ACL apply lag > 120 s; consumer lag > 1000 for 10 min; availability burn rate 14.4x over 1 h and 6x over 6 h. The DEFAULT-partition alert window is 30 min, and the `maintenance` job runs every 15 min in demo mode (R76, R21). Notification channel: email to `alert_email` (R75).

Alerts: availability burn rate (thresholds above), degraded turns > 5% in 15 min, rerank 429 > 0, LLM fallback in use, outbox oldest age, ACL applier lag, consumer lag, DLQ non-empty, DEFAULT partition non-empty, readiness failing, model retirement soon, budget alerts on the monthly cloud and LLM spend (thresholds set in E9 against the $100-200 budget). Dashboards in Cloud Monitoring (one per concern: chat, retrieval, events, cost). Epic E9.

### 9.6 Evaluation signals
Offline: Langfuse datasets and `run_experiment`. Online (L4): `chat-api` writes an `eval.sample.v1` outbox row for a `EVAL_SAMPLE_RATE` fraction (5-10%) of completed turns; the `eval-judge` worker consumes the topic, scores the redacted question / answer / cited excerpts with `claude-haiku-5-5` (judge differs from the answer model), and writes the scores to Langfuse and to the `eval_scores` table (tenant RLS). Thumbs feedback is stored in `feedback` and sent as `FeedbackRecorded`. Results flow to BigQuery through `eval.events.v1`. Langfuse-side evaluators are not used.
