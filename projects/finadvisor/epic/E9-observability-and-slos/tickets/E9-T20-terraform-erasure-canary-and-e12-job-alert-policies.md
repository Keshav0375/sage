---
key: "E9-T20"
title: "Terraform: erasure, canary and E12 job alert policies"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T11", "E9-T5", "E12-T7", "E12-T15", "E12-T21"]
arch_refs: ["deep-dive/09-observability.md#9.5", "deep-dive/09-observability.md#9.8", "deep-dive/04-components-and-responsibilities.md#4.8", "decision-logs.md#adr-029", "decision-logs.md#adr-030"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 219, "id": 6263618740, "url": "https://github.com/Keshav0375/FinAdvisor/issues/219"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Alert policies exist for a stuck erasure, an unconfirmed Langfuse delete, a FAILED canary and a failed execution of each E12 job.

## Description
Implements the lifecycle alerts of 9.5 ("`erasure_oldest_pending_age_s` > 4 h, `tombstone_violations_total` > 0 (E9-T19), ... a Langfuse delete not honoured after 24 h") and 9.8 (the canary), plus alerting on the E12 jobs of 4.8. Add terraform/alerts_lifecycle.tf with the E9-T11 channel and the `ticket` or `page` user_label convention of E9-T19:
- `erasure_oldest_pending_age_s` > 14400 s (4 h) for 5 min, page (ADR-029, ADR-030).
- `erasure_langfuse_unconfirmed`: increase > 0 over 1 h, ticket (E12-T15 emits it once when a delete is still not honoured at 24 h; the receipt stays at phase 1).
- FAILED canary (R4-D20, E12-T21: "A store that does not reach zero inside its documented window is a FAILED canary: the drill reports the store and its age, raises the E9 alert metric `canary_failed`"): `canary_failed` increase > 0 over 1 h, page. Because the canary runs only at demo start, the condition uses a 1 h window and missing data is inactive; the policy documentation shows the failed store and age from the drill's log line (the notification `documentation` field names the log query).
- E12 job failures: for each of `reconcile`, `erasure-verify`, `erasure-canary`, `purge-source`, `embed-backfill` and `ledger-export` (the E12 jobs of 4.8 that run on a schedule or at demo start), a policy on failed Cloud Run job executions (`run.googleapis.com/job/completed_execution_count` with `result = failed`) increase > 0 over 1 h, ticket; the job list is a tfvar `e12_job_names`. A job that is not running because the system is stopped raises nothing (`EVALUATION_MISSING_DATA_INACTIVE`).
- Thresholds are tfvars with these defaults.
Out of scope: the metrics' emitters (E12), reconcile and tombstone alerts (E9-T19), the drill (E9-T23).

## Acceptance criteria
- [ ] Given terraform plan, Then policies exist for erasure_oldest_pending_age, erasure_langfuse_unconfirmed, canary_failed and one per name in `e12_job_names` (6), 9 in all, asserted by scripts/check_monitoring_tf.py.
- [ ] Given the erasure age policy JSON, Then the threshold is 14400 and the severity label is page; given canary_failed Then the severity label is page and `evaluation_missing_data` is EVALUATION_MISSING_DATA_INACTIVE.
- [ ] Given a job name removed from `e12_job_names`, When the check script runs against the arch job table list (reconcile, erasure-verify, erasure-canary, purge-source, embed-backfill, ledger-export), Then it exits non-zero naming the missing job.
- [ ] Given the E9-T23 drill sets `erasure_oldest_pending_age_s` to 15000 in a scratch project, Then the incident opens within 15 minutes (drill record).
