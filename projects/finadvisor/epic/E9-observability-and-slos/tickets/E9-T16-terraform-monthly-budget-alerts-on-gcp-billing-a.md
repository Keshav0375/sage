---
key: "E9-T16"
title: "Terraform: monthly budget alerts on GCP billing and LLM cost"
epic: "E9"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E9-T11", "E9-T6"]
arch_refs: ["deep-dive/09-observability.md#9.5"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
A billing budget plus an alert on llm_cost_usd_total cover monthly cloud and LLM spend against the $100-200 budget.

## Description
Implements deep-dive/09-observability.md §9.5: "budget alerts on the monthly cloud and LLM spend (thresholds set in E9 against the $100-200 budget)". Add terraform/budget.tf with google_billing_budget for the project: amount var monthly_budget_usd (default 150), notifications at 50%, 90% and 100% of actual spend and 100% forecasted, to the E9-T11 email channel. LLM spend (R73): add a google_monitoring_alert_policy on the cumulative monthly increase of llm_cost_usd_total (sum over provider and model, 30-day rolling window) with thresholds at 90% and 100% of var llm_monthly_budget_usd (default 75; the sum of monthly_budget_usd for cloud and LLM stays inside the $100-200 range, documented in docs/runbooks/slo.md). No manual check.

## Acceptance criteria
- [ ] Given terraform plan, Then one google_billing_budget exists with amount 150 USD and threshold rules 0.5, 0.9, 1.0 (actual) and 1.0 (forecasted) (plan JSON assertion).
- [ ] Given monthly_budget_usd=250 outside the 100-200 range, When terraform plan, Then a validation block fails with a message naming the range 100-200.
- [ ] Given billing_account variable unset, Then plan errors.
- [ ] Given the drill (E9-T17) lowers the budget to $1 in a scratch project, Then a notification arrives on the channel (drill record).
- [ ] Given the plan JSON, Then an alert policy on llm_cost_usd_total exists with thresholds equal to 0.9 and 1.0 times llm_monthly_budget_usd; in the drill, recording llm_cost_usd_total above that threshold opens the incident.
