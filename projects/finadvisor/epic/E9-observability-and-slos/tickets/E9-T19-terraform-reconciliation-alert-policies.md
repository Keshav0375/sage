---
key: "E9-T19"
title: "Terraform: reconciliation alert policies"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T11", "E9-T5", "E12-T22", "E12-T23"]
arch_refs: ["deep-dive/09-observability.md#9.7", "deep-dive/09-observability.md#9.5", "decision-logs.md#adr-034", "decision-logs.md#adr-029"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Alert policies exist for every reconciliation pair of 9.7, with ticket or page severity as the table says, and a stopped system raises nothing.

## Description
Implements deep-dive/09-observability.md 9.7 ("Reconciliation alerts", ADR-034). Add terraform/alerts_reconcile.tf using the E9-T11 channel. Severity is a policy `user_label` (`ticket` = WARNING, `page` = CRITICAL; both go to the one email channel, R75). Policies, on metrics of the E9-T5 registry:
- source to bronze: `reconcile_mismatch_total{pair="source_bronze"}` increase > 0 over 1 h, ticket (E12-T22 emits the metric only on the second consecutive run, so the "after 2 runs" rule lives in the emitter).
- bronze to silver and silver to Postgres chunks: increase > 0 for `bronze_silver` and `silver_chunks`, ticket.
- index: `ann_selfhit_rate` < 0.99 ticket, < 0.95 page.
- Postgres to BigQuery daily: `pg_bigquery` increase > 0, ticket.
- cell to cell: `public_manifest_drift` increase > 0, ticket (E13-T10).
- tombstones: `tombstone_violations_total` > 0, page.
- BigQuery settings: `reconcile_mismatch_total{pair="bq_settings"}` increase > 0, page (a dataset without `max_time_travel_hours = 48`).
Conditions use `evaluation_missing_data = EVALUATION_MISSING_DATA_INACTIVE` and never a metric-absence condition: reconcile runs only while the system is up, a stopped system raises no alert and the first run at the next start catches up (9.7). Pair names live in one tfvar map `reconcile_pairs`; scripts/check_monitoring_tf.py fails if a `pair` literal passed to `record("reconcile_mismatch_total", ...)` in backend/src is not a key of that map.
Out of scope: the reconcile job (E12-T22, E12-T23), dashboards (E9-T18).

## Acceptance criteria
- [ ] Given terraform plan, Then exactly 9 policies exist (source_bronze, bronze_silver, silver_chunks, index ticket, index page, pg_bigquery, cell drift, tombstones, bq_settings) each with its user_label severity, asserted by `terraform show -json` in scripts/check_monitoring_tf.py.
- [ ] Given the policy JSON for the index pair, Then thresholds are 0.99 (ticket) and 0.95 (page); for tombstones threshold 0 comparison GT and severity page.
- [ ] Given every policy JSON, Then `evaluation_missing_data` is EVALUATION_MISSING_DATA_INACTIVE and no `condition_absent` block exists (script assertion), so a stopped system cannot raise an alert.
- [ ] Given a `record("reconcile_mismatch_total", 1, pair="made_up")` literal in a test fixture tree, When the check script runs, Then it exits non-zero naming the pair.
