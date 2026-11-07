---
key: "E9-T12"
title: "Terraform: four Cloud Monitoring dashboards"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T11"]
arch_refs: ["deep-dive/09-observability.md#9.5", "deep-dive/09-observability.md#9.2", "deep-dive/09-observability.md#9.9", "decision-logs.md#adr-039"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Dashboards chat, retrieval, events and cost exist as code; with the data-lifecycle dashboard of E9-T18 they show every 9.2 metric.

## Description
Implements deep-dive/09-observability.md §9.5: "Dashboards in Cloud Monitoring (one per concern: chat, retrieval, events, cost, data lifecycle)". This ticket builds the first four in terraform/dashboards/*.json and google_monitoring_dashboard resources in terraform/dashboards.tf; the fifth is E9-T18.
- chat: chat_ttft_ms and chat_total_ms p50/p95 with the SLO lines (3.5 s, 2.0 s, 8 s), gate_refusals_total, guard_blocks_total by guard, llm_fallback_total, llm_breaker_state, answer_cache_hit_ratio, error rate; guardrail panels (9.9): guard_hits_total by guard and reason, guard_skipped_total (Model Armor `EXECUTION_SKIPPED`), guard_latency_ms p95 per guard with a 150 ms line, numeric_gate_reject_total by reason, citation_rejected_total, guard_precision and guard_recall (weekly gauges, shown as last value with the measurement date).
- retrieval: retrieval_first_stage_ms and rerank_ms p95 with lines at 600 and 700 ms (first stage target is 600 ms, ADR-039 M3), rerank_fallback_total by reason, rerank_429_total, retrieval_degraded_ratio.
- events: outbox_oldest_age_s, outbox_unpublished, consumer_lag by group, acl_apply_lag_s, dlq_messages_total, default_partition_rows.
- cost: db_connections_in_use against 300, tenant_budget_rejections_total by tenant, llm_cost_usd_total, Kong prometheus series, billing spend widget.
Each dashboard's metric names come from the registry attribute `dashboard` (E9-T5); Kong prometheus series appear only where exported.

## Acceptance criteria
- [ ] Given the E9-T5 registry, When scripts/check_monitoring_tf.py runs, Then every registry name whose `dashboard` attribute is chat, retrieval, events or cost appears in the matching dashboard JSON; the check fails if one is missing.
- [ ] Given terraform validate, When run in CI, Then it passes; given terraform apply to a scratch project in the drill, Then four dashboards are listed by gcloud monitoring dashboards list.
- [ ] Given the chat dashboard JSON, When parsed, Then threshold lines of 3500, 2000 and 8000 ms exist on the TTFT and total charts and a 150 ms line exists on the guard latency chart (jq assertions in the check script).
- [ ] Given the retrieval dashboard JSON, Then threshold lines at 600 and 700 ms exist and no line at 300 ms.
