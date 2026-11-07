---
key: "E9-T16"
title: "Terraform: monthly budget alerts on GCP billing and LLM cost"
epic: "E9"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E9-T11", "E9-T6"]
arch_refs: ["deep-dive/09-observability.md#9.5", "deep-dive/02-quality-attributes.md#2.5", "deep-dive/06-interfaces-and-contracts.md#6.6", "decision-logs.md#adr-018"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
A billing budget alerts at $180 a month against the $200 ceiling, and an alert on llm_cost_usd_total covers the LLM share.

## Description
Implements deep-dive/09-observability.md §9.5: "a $180/month total alert guards the $200 ceiling (R4-D16, `BUDGET_ALERT_USD`), plus the LLM share (`LLM_MONTHLY_BUDGET_USD` 75) from GCP billing and `llm_cost_usd_total`; eval runs are capped by `EVAL_BUDGET_USD`" and 2.5 ("$180/month total guards the $200 ceiling"). Config values (06 6.6): `BUDGET_ALERT_USD` = 180, `LLM_MONTHLY_BUDGET_USD` = 75.

Add terraform/budget.tf with google_billing_budget for the project: amount var `monthly_ceiling_usd` (default 200, the ceiling), notifications at 50% of the ceiling, at `budget_alert_usd / monthly_ceiling_usd` (var `budget_alert_usd`, default 180, so 90%) , at 100% of actual spend, and 100% forecasted, to the E9-T11 email channel. LLM spend (R73): add a google_monitoring_alert_policy on the cumulative monthly increase of llm_cost_usd_total (sum over provider and model, 30-day rolling window) with thresholds at 90% and 100% of var `llm_monthly_budget_usd` (default 75). Document the values in docs/runbooks/slo.md: the demo-month bound of $100-200 and the expected $110-160 are unchanged (R4-D16); the $180 line is the alert, not the budget. No manual check.

## Acceptance criteria
- [ ] Given terraform plan, Then one google_billing_budget exists with amount 200 USD and threshold rules 0.5, 0.9 (equal to 180 / 200), 1.0 (actual) and 1.0 (forecasted) (plan JSON assertion).
- [ ] Given budget_alert_usd=210 above the ceiling of 200, When terraform plan, Then a validation block fails naming the ceiling; given budget_alert_usd=180 it passes.
- [ ] Given billing_account variable unset, Then plan errors.
- [ ] Given the drill (E9-T17) lowers the ceiling to $1 in a scratch project, Then a notification arrives on the channel (drill record).
- [ ] Given the plan JSON, Then an alert policy on llm_cost_usd_total exists with thresholds equal to 0.9 and 1.0 times llm_monthly_budget_usd (75); in the drill, recording llm_cost_usd_total above that threshold opens the incident.
