---
key: "E9-T18"
title: "Terraform: data-lifecycle dashboard for erasure, receipts and canary"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T12", "E9-T5", "E12-T16", "E12-T21", "E12-T23"]
arch_refs: ["deep-dive/09-observability.md#9.7", "deep-dive/09-observability.md#9.8", "deep-dive/09-observability.md#9.2", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.14", "decision-logs.md#adr-030", "decision-logs.md#adr-034"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 216, "id": 6263615699, "url": "https://github.com/Keshav0375/FinAdvisor/issues/216"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
A fifth dashboard shows erasure windows per store, deletion receipts, the demo-start canary, reconciliation findings and ingest health.

## Description
Implements 9.5 ("Dashboards ... chat, retrieval, events, cost, data lifecycle") for 9.7 and 9.8. Add terraform/dashboards/lifecycle.json and a `google_monitoring_dashboard` in terraform/dashboards.tf. Panels (metric names from the E9-T5 registry, `dashboard: lifecycle`):
- Erasure windows per store: one row per store (Postgres, index, cache, GCS, Langfuse, Kafka, BigQuery) with its documented window as a threshold line from deep-dive/05-1 5.14 (live stores immediate, Langfuse 24 h alert line, Kafka about 8 d, BigQuery 14 d), fed by `erasure_oldest_pending_age_s` and the per-store canary time-to-zero series of E12-T21; BigQuery fail-safe, Cloud SQL PITR logs and provider retention are shown as text panels labelled `documented` or `provider`, never as measured series (9.8).
- Deletion receipts: `erasure_receipts_open` (waiting for phase 2) over time, and a table-style text panel linking the receipt object prefix.
- Canary at demo start: last canary result, per-store time to zero, `canary_failed` count; the dashboard notes that the canary runs at each demo start, not on a cron, so gaps between starts are expected.
- Reconciliation: `reconcile_mismatch_total` by `pair`, `ann_selfhit_rate` with lines at 0.99 and 0.95, `tombstone_violations_total` (must be 0).
- Ingest: `source_frozen`, `connector_listing_items`, `source_silent_edit_total` by source_id, `quarantined_total` by reason, `llm_egress_refused_total`.
Out of scope: alert policies (E9-T19 to E9-T21).

## Acceptance criteria
- [ ] Given the E9-T5 registry, When scripts/check_monitoring_tf.py runs, Then every name with `dashboard: lifecycle` appears in lifecycle.json and, together with E9-T12, every registry name appears on at least one dashboard; the check fails if one is missing.
- [ ] Given lifecycle.json parsed with jq, Then `ann_selfhit_rate` has threshold lines 0.99 and 0.95, and the erasure window panel has a 24 h line for Langfuse and a 14 d line for BigQuery.
- [ ] Given lifecycle.json, Then no series or panel title presents BigQuery fail-safe, Cloud SQL PITR or provider retention as a measured value (jq assertion that those names occur only in text panels).
- [ ] Given terraform validate in CI, Then it passes; given apply to a scratch project in the drill, Then five dashboards are listed by gcloud monitoring dashboards list.
