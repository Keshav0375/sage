---
key: "E9-T5"
title: "Shared metrics module and 9.2 metric registry"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T1", "E9-T2", "E3-T9"]
arch_refs: ["deep-dive/09-observability.md#9.2", "decision-logs.md#adr-018", "decision-logs.md#adr-034", "decision-logs.md#adr-036"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
One module owns metric names, types and labels from the whole 9.2 table (including the round-4 rows) and records them to OTel and to a log line for log-based metrics.

## Description
Implements deep-dive/09-observability.md §9.2: "Metrics (log-based and OTel, in Cloud Monitoring)". Create backend/src/observability/metrics.py:
- A registry listing every metric in the 9.2 table with name, kind (counter, histogram, gauge), unit, allowed labels and a `dashboard` attribute (chat, retrieval, events, cost or lifecycle, used by E9-T12 and E9-T18). The set is the table as it stands, not a hard-coded count: the original rows (chat_ttft_ms, chat_total_ms, retrieval_first_stage_ms, rerank_ms, rerank_fallback_total{reason}, rerank_429_total, retrieval_degraded_ratio, gate_refusals_total, guard_blocks_total{guard}, llm_fallback_total, llm_breaker_state, answer_cache_hit_ratio, outbox_oldest_age_s, consumer_lag{group}, acl_apply_lag_s, dlq_messages_total, tenant_budget_rejections_total{tenant}, default_partition_rows, db_connections_in_use, llm_cost_usd_total{provider,model}, readiness_failing, model_retirement_days, citation_rejected_total, outbox_unpublished) plus the round-4 rows: guard_hits_total{guard,reason}, guard_skipped_total, guard_latency_ms{guard}, quarantined_total{reason}, numeric_gate_reject_total{reason}, guard_precision{guard}, guard_recall{guard}, reconcile_mismatch_total{pair}, ann_selfhit_rate, tombstone_violations_total, erasure_oldest_pending_age_s, erasure_receipts_open, source_frozen{source_id,reason}, connector_listing_items{source_id}, source_silent_edit_total{source_id}, llm_egress_refused_total (R4-D20 Q9: names follow the E11 tickets; the 9.2 table adopts them), and the E12/E13 rows `canary_failed`, `erasure_langfuse_unconfirmed`, `public_manifest_drift`, `canary_time_to_zero_s{store}` (name as E12-T21 fixes it).
- The E11 and E12 emitters keep their ticket names (R4-D20 Q9) and the 9.2 table adopts them, so there is no separate extras list: registry names equal the table. Kong `prometheus` series are not in the registry.
- record(name, value, **labels) that rejects unknown names or labels and records through the OTel metrics API (OTLP) and also writes one structured log line (event='metric', metric, value, labels) through the E9-T1 logger so log-based metrics work.
- Existing emitters from E3-T9, E4, E5, E11 and E12 are migrated to call record() where they currently do something else; do not change their values.
Out of scope: dashboards (E9-T12, E9-T18), alerts (E9-T14, E9-T15, E9-T19 to E9-T21), new emitters (E9-T6, E9-T7, E9-T22).

## Acceptance criteria
- [ ] Given record('not_a_metric', 1), When called, Then it raises KeyError; given record('rerank_fallback_total', 1, reason='x', extra='y'), Then it raises on the unknown label (pytest test_metrics_registry.py).
- [ ] Given the registry, When compared with the metric names parsed from the deep-dive/09-observability.md §9.2 table copied into backend/tests/observability/metrics_9_2.txt, Then registry names equal the parsed set (the test fails if a row is added or missing on either side).
- [ ] Given record('chat_ttft_ms', 1200), When captured, Then one OTel data point and one log line with event='metric', metric='chat_ttft_ms' and value 1200 exist.
- [ ] Given a label value tenant_id longer than 64 chars or containing newline, When recorded, Then it is rejected or truncated so the log line stays a single JSON line.
- [ ] Given record('guard_precision', 0.97, guard='presidio') and record('erasure_oldest_pending_age_s', 5), When captured, Then both are accepted; record('guard_precision', 0.9, guard='x', class='y') raises on the unknown label; every registry entry has a `dashboard` value from the allowed five.
