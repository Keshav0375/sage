---
key: "E9-T13"
title: "Terraform: availability and latency SLOs with burn-rate alerts"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T11", "E9-T6"]
arch_refs: ["deep-dive/09-observability.md#9.5", "decision-logs.md#adr-018", "decision-logs.md#adr-039"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
SLOs for availability (prod only), latency and retrieval exist with multi-window burn-rate alerts whose thresholds are fixed in the ticket.

## Description
Implements deep-dive/09-observability.md §9.5 SLO table: availability 99.5% monthly of chat requests not failing, prod profile only; TTFT p95 < 3.5 s (p50 < 2.0 s) and full answer p95 < 8 s on demo and prod; retrieval first stage p95 <= 600 ms, rerank p95 < 700 ms on both ("Windows and thresholds set in E9"). The first-stage target is 600 ms, not the earlier 300 ms: embed then hybrid SQL is serial (0.25 + 0.30 s estimated) and ADR-039 M3 rejected the MVP's 300 ms; TTFT targets are unchanged.
Add google_monitoring_slo resources in terraform/slo.tf over a custom service for chat-api. Availability SLO created only when env_profile == "prod" (count). Burn-rate alert policies: fast (1 h window with 5 min lookback, burn rate 14.4) and slow (6 h window with 30 min lookback, burn rate 6), the standard multi-window values for a 99.5% target; record the choice and the budget (0.5% of a 30-day window = about 3.6 h) in docs/runbooks/slo.md. A chat request fails when the response is HTTP 5xx or the SSE stream ends with an error event other than the intended refusals/4xx codes; define the good/total filter in the doc.
Out of scope: other alerts.
Burn-rate numbers fixed by R72: 14.4x over 1 h and 6x over 6 h.

## Acceptance criteria
- [ ] Given env_profile=prod, When terraform plan, Then one availability SLO with goal 0.995 and rolling 30-day period and two burn-rate alert policies are planned; given env_profile=demo, Then the availability SLO and its alerts are absent and the latency SLOs remain (CI plan assertions through terraform show -json).
- [ ] Given the plan JSON, When checked, Then the latency SLO thresholds are 3500 ms (p95), 2000 ms (p50), 8000 ms and retrieval 600 and 700 ms; a threshold of 300 for the first stage fails the check.
- [ ] Given docs/runbooks/slo.md, When reviewed, Then it states the two windows, burn rates 14.4 and 6, and the failing-request definition (checked by a presence test in scripts/check_monitoring_tf.py).
- [ ] Given the drill in E9-T17 injects a 20% error rate for 10 min in a scratch prod-profile project, Then the fast burn alert opens.
