> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 9. Observability

### 9.1 Traces
- OpenTelemetry end to end: Kong `opentelemetry` (`traceparent`) to `chat-api` (FastAPI, asyncpg / SQLAlchemy, Voyage and Anthropic HTTP calls) to workers (`traceparent` carried in Kafka headers) to Cloud Trace (free to 2.5M spans/month). SQL parameter capture off; no request bodies in spans (D13o).
- Span names: `chat.turn`, `auth.verify`, `principal.load`, `guard.input`, `guard.model_armor`, `guard.numeric_gate`, `guard.footer`, `embed.query`, `retrieval.hybrid_sql`, `retrieval.rerank`, `retrieval.gate`, `llm.stream`, `guard.output`, `persist.turn`, `outbox.relay`, `consumer.<role>`, `ingest.scan`, `connector.<source>`, `reconcile.<pair>`, `erasure.<store>`.
- Langfuse Cloud (Python SDK 5.x, behind one wrapper; the v2 `trace()/span()/generation()` calls are gone, G-15): one trace per turn with generations (model, usage, cache read), retrieval span (chunk ids, scores), gate result. `@observe` with `capture_input=False` / `capture_output=False` on sensitive spans and `mask_otel_spans` for export masking (the legacy `mask=` does not cover OTel spans); input is scrubbed text only; tagged by `tenant_id`; never blocks the request path.

### 9.2 Metrics (log-based and OTel, in Cloud Monitoring)

| Metric | Meaning |
|---|---|
| `chat_ttft_ms`, `chat_total_ms` | TTFT and full answer latency (SLO inputs) |
| `retrieval_first_stage_ms`, `rerank_ms` | embed + SQL, rerank latency |
| `rerank_fallback_total{reason}`, `rerank_429_total`, `retrieval_degraded_ratio` | rerank fallbacks, rate limits and the share of degraded turns |
| `gate_refusals_total` | confidence gate refusals |
| `guard_blocks_total{guard}` | Model Armor, input cap, citation verifier, PII blocks |
| `guard_hits_total{guard,reason}`, `guard_skipped_total`, `guard_latency_ms{guard}` | per-guardrail hits, `EXECUTION_SKIPPED` and latency, against the 150 ms p95 rule of §2.1 (ADR-036) |
| `quarantined_total{reason}` | versions quarantined by the ingest scan or a contract rule |
| `numeric_gate_reject_total{reason}` | answers withheld by the numeric grounding gate, by reason |
| `guard_precision{guard}`, `guard_recall{guard}` | measured weekly by the eval run on the sets of §2.10 and written as gauges; a measurement, not a live rate |
| `reconcile_mismatch_total{pair}`, `ann_selfhit_rate` | reconciliation findings per pair; ANN self-hit canary (§9.7) |
| `tombstone_violations_total` | tombstoned data found present in a store; must be 0 |
| `erasure_oldest_pending_age_s`, `erasure_receipts_open` | oldest `deletion_requests` row not executed (pages > 4 h); receipts waiting for phase 2 |
| `connector_frozen{source}`, `connector_listing_items{source}`, `silent_edit_total{source}` | breaker state, last listing size, silent edits |
| `llm_egress_refused_total` | private ingest refused because `llm_egress_ack` is false |
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
| Retrieval | first stage p95 <= 600 ms, rerank p95 < 700 ms | both |

Alert thresholds (ADR-025 R72): outbox oldest age > 300 s; ACL apply lag > 120 s; consumer lag > 1000 for 10 min; availability burn rate 14.4x over 1 h and 6x over 6 h. The DEFAULT-partition alert window is 30 min, and the `maintenance` job runs every 15 min in demo mode (R76, R21). Notification channel: email to `alert_email` (R75).

Alerts: availability burn rate (thresholds above), degraded turns > 5% in 15 min, rerank 429 > 0, LLM fallback in use, outbox oldest age, ACL applier lag, consumer lag, DLQ non-empty, DEFAULT partition non-empty, readiness failing, model retirement soon, the reconciliation alerts of §9.7, `erasure_oldest_pending_age_s` > 4 h, `tombstone_violations_total` > 0, a frozen connector, a Langfuse delete not honoured after 24 h, and the budget alerts: a **$180/month total alert guards the $200 ceiling** (R4-D16, `BUDGET_ALERT_USD`), plus the LLM share (`LLM_MONTHLY_BUDGET_USD` 75) from GCP billing and `llm_cost_usd_total`; eval runs are capped by `EVAL_BUDGET_USD`. Dashboards in Cloud Monitoring (one per concern: chat, retrieval, events, cost, data lifecycle). Epic E9, with E12 for the lifecycle alerts.

### 9.6 Evaluation signals
Offline: Langfuse datasets and `run_experiment`. Online (L4): `chat-api` writes an `eval.sample.v1` outbox row (ids, chunk ids, hashes and flags, no text) for a `EVAL_SAMPLE_RATE` fraction (5-10%) of completed turns; the `eval-judge` worker consumes the topic, reads the redacted question / answer / cited excerpts from Postgres `messages` by `message_id` under the tenant's role (a message that has been erased is skipped), scores them with `claude-haiku-5-5` (judge differs from the answer model), and writes the scores to Langfuse and to the `eval_scores` table (tenant RLS). Thumbs feedback is stored in `feedback` and sent as `FeedbackRecorded`. Results flow to BigQuery through `eval.events.v1`. Langfuse-side evaluators are not used.

### 9.7 Reconciliation alerts (ADR-034)

Job `reconcile` runs hourly only while the system runs and compares only versions idle > 30 min. A stopped system raises no alert; the first run at the next start catches up. Manifests are keyed on `parser_version`, so a parser bump is a planned re-baseline event, not an alert storm. Exact equality, no tolerance.

| Pair | Check | Alert |
|---|---|---|
| source to bronze | every `present` observation has a GCS object whose sha256 metadata equals the observation | ticket after 2 runs |
| bronze to silver | `n_chunks` and `chunk_set_hash = sha256(sorted(chunk_hash))` per version | ticket |
| silver to Postgres chunks | same count and hash recomputed from `chunks`; every child has an embedding for the active `embed_model` | ticket |
| index | ANN self-hit canary: 50 sampled chunks queried with their own vectors return themselves in the top 5; `ann_selfhit_rate` >= 0.99 | page below 0.95 |
| Postgres to BigQuery | per day `count` and `md5(string_agg(event_id ORDER BY event_id))` of published outbox rows vs `ingest_events` | ticket |
| cell to cell | PUBLIC manifest (document count and `chunk_set_hash` per version) equal | ticket on drift |
| tombstones | absence in Postgres, GCS, BigQuery (current), Langfuse and cache; hourly for 24 h after any erasure, then daily | page |
| BigQuery settings | every dataset, including dbt-created ones, has `max_time_travel_hours = 48` | page |

### 9.8 Deletion receipts and the canary at demo start (ADR-030, R4-D9)

- Receipts: phase 1 "executed" from `erasure_steps` within hours; phase 2 "windows closed" after each store's window, signed by `erasure-verify`. `erasure_receipts_open` shows what waits for phase 2. A Langfuse delete that is not honoured is retried, alerts at 24 h and leaves the receipt at phase 1.
- Canary: `demo-up` runs the erasure job first, then drives a synthetic canary advisor with unique tokens through chat, a trace, events and BigQuery, erases it and records when each observable store reaches zero. It runs at each demo start, not on a weekly cron, because the system is often stopped. Compose runs the same drill nightly minus provider windows.
- Not observed: the BigQuery fail-safe, Cloud SQL PITR logs and provider retention are documented windows; the canary and receipts mark them `documented` or `provider`, never measured (§6.9).

### 9.9 Guardrail measurement (ADR-036, ADR-037)

Precision, recall and latency per guardrail are measured weekly on the eval sets of §2.10 (PII, direct injection, indirect injection, golden-200 slices) and exported as the gauges of §9.2, with live counters for hits, skips and latency. Rule: a guard whose p95 adds more than 150 ms to the critical path moves to async-after-first-sentence or is dropped. Numeric-gate false rejects on correct answers are tracked against the proposed 3% line. Model Armor latency is measured from the Cloud Run region before its timeout is fixed (§10).
