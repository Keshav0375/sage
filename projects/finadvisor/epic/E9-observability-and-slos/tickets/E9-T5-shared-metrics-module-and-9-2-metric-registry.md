---
key: "E9-T5"
title: "Shared metrics module and 9.2 metric registry"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T1", "E9-T2", "E3-T9"]
arch_refs: ["deep-dive/09-observability.md#9.2", "ADR-018"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
One module owns metric names, types and labels from the 9.2 table and records them to OTel and to a log line for log-based metrics.

## Description
Implements deep-dive/09-observability.md §9.2: "Metrics (log-based and OTel, in Cloud Monitoring)". Create backend/src/observability/metrics.py:
- A registry listing every metric in the table with name, kind (counter, histogram, gauge), unit and allowed labels: chat_ttft_ms, chat_total_ms, retrieval_first_stage_ms, rerank_ms, rerank_fallback_total{reason}, rerank_429_total, retrieval_degraded_ratio, gate_refusals_total, guard_blocks_total{guard}, llm_fallback_total, llm_breaker_state, answer_cache_hit_ratio, outbox_oldest_age_s, consumer_lag{group}, acl_apply_lag_s, dlq_messages_total, tenant_budget_rejections_total{tenant}, default_partition_rows, db_connections_in_use.
- record(name, value, **labels) that rejects unknown names or labels and records through the OTel metrics API (OTLP) and also writes one structured log line (event='metric', metric, value, labels) through the E9-T1 logger so log-based metrics work.
- Existing emitters from E3-T9, E4 and E5 are migrated to call record() where they currently do something else; do not change their values.
Out of scope: dashboards, alerts, new emitters (E9-T6, E9-T7).
Add to the registry (resolutions R73, R74): llm_cost_usd_total{provider,model} (counter, USD), readiness_failing (gauge 0/1) and model_retirement_days (gauge, days until the earliest retirement of a configured model). The registry now has 22 metrics; the 9.2 table copy in backend/tests/observability/metrics_9_2.txt includes these three (the architecture table §9.2 gains these rows). Earlier epics emit with plain OTel meters; this ticket moves them to the registry (R71).

## Acceptance criteria
- [ ] Given record('not_a_metric', 1), When called, Then it raises KeyError; given record('rerank_fallback_total', 1, reason='x', extra='y'), Then it raises on the unknown label (pytest test_metrics_registry.py).
- [ ] Given the registry, When compared with the metric names parsed from the deep-dive/09-observability.md §9.2 table copied into backend/tests/observability/metrics_9_2.txt, Then the sets are equal (the test fails if one is added or missing).
- [ ] Given record('chat_ttft_ms', 1200), When captured, Then one OTel data point and one log line with event='metric', metric='chat_ttft_ms' and value 1200 exist.
- [ ] Given a label value tenant_id longer than 64 chars or containing newline, When recorded, Then it is rejected or truncated so the log line stays a single JSON line.
- [ ] Given record('llm_cost_usd_total', 0.01, provider='anthropic', model='x'), When captured, Then it is accepted; with a label other than provider and model it raises; the registry has exactly the 22 names in metrics_9_2.txt.
