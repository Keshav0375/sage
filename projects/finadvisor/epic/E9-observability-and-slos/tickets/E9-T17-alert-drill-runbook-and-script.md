---
key: "E9-T17"
title: "Alert drill runbook and script"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T13", "E9-T14", "E9-T15", "E9-T16"]
arch_refs: ["deep-dive/09-observability.md#9.5"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
A script and runbook fire each 9.5 alert in a scratch project and record the result, covering the Done-when drill.

## Description
Implements the Done-when item: "Each alert in deep-dive/09-observability.md#9.5 fires in a drill (degraded turns > 5% in 15 min, rerank 429, outbox age, ACL applier lag, DEFAULT partition non-empty, readiness failure, budget)". Add scripts/alert_drill.py and docs/runbooks/alert-drills.md. The script takes an alert name, injects the condition (writes the matching log-metric line or metric value for the alert; real fault injection where cheap: stop acl-applier, insert a DEFAULT partition row, flip a role flag for readiness, lower budget), polls the Cloud Monitoring API until an incident opens or a timeout (default 15 min), then clears the condition and reports PASS or FAIL as JSON. Include the burn-rate, LLM fallback, consumer lag, DLQ and model-retirement alerts too. The runbook records the date, result and incident link per alert, and a manual check that the E9-T10 trace appears in Cloud Trace.
Runs only against the scratch project named by a required --project argument and refuses ENV_PROFILE=prod project ids listed in a deny var.
The drill also covers the llm_cost_usd_total budget alert and the model_retirement_days alert; the DEFAULT-partition drill waits up to 45 min.

## Acceptance criteria
- [ ] Given a scratch project with E9-T11 to E9-T16 applied, When python scripts/alert_drill.py --all runs, Then each alert in deep-dive/09-observability.md §9.5 returns PASS in the JSON and the process exits 0; exit non-zero if any fails.
- [ ] Given a project where one policy is removed, When the script runs, Then that alert reports FAIL (negative control).
- [ ] Given --project equals a name in the deny list, Then the script exits 2 without calling any API (unit test).
- [ ] Given docs/runbooks/alert-drills.md, Then it has a row per alert in 9.5 (presence test in scripts/check_monitoring_tf.py).
