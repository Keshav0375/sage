---
key: "E9-T23"
title: "Extend the alert drill to the round-4 alerts"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T17", "E9-T16", "E9-T19", "E9-T20", "E9-T21"]
arch_refs: ["deep-dive/09-observability.md#9.5", "deep-dive/09-observability.md#9.7", "deep-dive/09-observability.md#9.8", "decision-logs.md#adr-018", "decision-logs.md#adr-029"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 222, "id": 6263621341, "url": "https://github.com/Keshav0375/FinAdvisor/issues/222"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Fire each new round-4 alert in a scratch project and record PASS or FAIL.

## Description
Added to the E9 Done-when (R4 changes): "each new alert fires in a drill; no log or span contains PII". Extend scripts/alert_drill.py and docs/runbooks/alert-drills.md from E9-T17 with these alerts: the reconcile pairs and index thresholds (E9-T19: a planted `reconcile_mismatch_total` increase per pair, `ann_selfhit_rate` at 0.98 for ticket and 0.94 for page), `tombstone_violations_total` = 1, `erasure_oldest_pending_age_s` = 15000, `erasure_langfuse_unconfirmed`, `canary_failed`, an E12 job failure (a deliberately failing `reconcile` execution in the scratch project), `source_frozen`, the quarantine ratio, `source_silent_edit_total`, and the $180 budget alert (the ceiling lowered so that 90% is crossed, E9-T16). Real fault injection where cheap (a failing job execution, a planted mismatch row); a metric write otherwise, through `metrics.record` in the scratch project. The drill also checks the missing-data rule: with the reconcile job stopped for the whole window, none of the reconcile policies opens an incident. Same safety as E9-T17: only the scratch project named by `--project`, the deny list applies.
Out of scope: the policies (E9-T19 to E9-T21), the PII leak test of logs and spans (E9-T9).

## Acceptance criteria
- [ ] Given a scratch project with E9-T16 and E9-T19 to E9-T21 applied, When `python scripts/alert_drill.py --round4` runs, Then each alert named above returns PASS in the JSON and the process exits 0, non-zero if any fails.
- [ ] Given a project where the canary_failed policy is removed, When the script runs, Then that alert reports FAIL (negative control).
- [ ] Given the reconcile job stopped for the whole drill window, When the missing-data case runs, Then no reconcile incident opens and the case reports PASS.
- [ ] Given docs/runbooks/alert-drills.md, Then it has a row per round-4 alert with date, result and incident link (presence test in scripts/check_monitoring_tf.py).
- [ ] Given --project equals a deny-list name, Then the script exits 2 without calling any API (unit test).
