---
key: "E9-T14"
title: "Terraform: chat and retrieval alert policies"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T11", "E9-T8", "E0-T4"]
arch_refs: ["deep-dive/09-observability.md#9.5"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Alert policies exist for degraded turns, rerank 429, LLM fallback, readiness failing and model retirement.

## Description
Implements these alerts from deep-dive/09-observability.md §9.5: "degraded turns > 5% in 15 min, rerank 429 > 0, LLM fallback in use, readiness failing, model retirement soon".
Add terraform/alerts_chat.tf with google_monitoring_alert_policy resources using the E9-T11 notification channel:
- degraded_turns: retrieval_degraded_ratio > 0.05 over a 15 min window.
- rerank_429: rate of rerank_429_total > 0 over 5 min.
- llm_fallback_in_use: llm_fallback_total increase > 0 over 5 min.
- readiness_failing: readiness_failing = 1 for 3 min (metric from E9-T8).
- model_retirement_soon: model_retirement_days (gauge, R74) < 30 for 5 min; the alert is on the gauge, not a log line.
Thresholds are tfvars with these defaults.

## Acceptance criteria
- [ ] Given terraform plan, When listed, Then five policies exist with the names above (terraform show -json assertion in scripts/check_monitoring_tf.py).
- [ ] Given the degraded_turns policy JSON, Then threshold 0.05 and duration 900 s.
- [ ] Given the E9-T17 drill emits rerank_429_total=1, When 5 minutes pass, Then the rerank_429 incident opens (drill record in docs/runbooks/alert-drills.md).
- [ ] Given the drill stops /readyz (DB role flag changed), Then readiness_failing opens within 5 minutes.
- [ ] Given the policy JSON for model_retirement_soon, Then its condition metric is model_retirement_days with threshold 30 and comparison LT (script assertion); no log-based metric is used for it.
