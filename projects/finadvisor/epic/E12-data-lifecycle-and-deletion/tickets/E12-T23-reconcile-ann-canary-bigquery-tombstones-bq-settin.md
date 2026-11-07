---
key: "E12-T23"
title: "reconcile: ANN canary, BigQuery, tombstones, BQ settings"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T22", "E12-T13", "E3-T4"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.22", "deep-dive/09-observability.md#9.7", "decision-logs.md#adr-34", "decision-logs.md#adr-30", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#28"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 301, "id": 6263781815, "url": "https://github.com/Keshav0375/FinAdvisor/issues/301"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add the ANN self-hit canary, the daily outbox to BigQuery check, the tombstone invariant and the time-travel settings check.

## Description
Extend `reconcile` with: (a) index: sample 50 chunks, query each with its own vector through the HNSW path of the active generation, expect itself in the top 5; emit `ann_selfhit_rate`; ticket below `ANN_SELFHIT_TICKET` 0.99, page below `ANN_SELFHIT_PAGE` 0.95; (b) Postgres to BigQuery daily: `count` and `md5(string_agg(event_id ORDER BY event_id))` of published outbox rows vs `ingest_events` for the day (ticket); (c) tombstones: for every ledger row absence in Postgres, GCS, BigQuery current rows, Langfuse and the answer cache; hourly for 24 h after any erasure, then daily; `tombstone_violations_total` must be 0, any violation pages; (d) BigQuery settings: `check_bq_time_travel()` from E12-T13, page on violation. Out of scope: Terraform alert policies (E9).

## Acceptance criteria
- [ ] Given an HNSW index deliberately broken (dropped or built over shuffled vectors) in a fixture DB, when the canary runs, then `ann_selfhit_rate` is below 0.95 and the page metric fires; on a healthy index it is at least 0.99 (#28).
- [ ] Given one extra row in `ingest_events` for the day, when the check runs, then count or md5 differs and a finding is raised; equal sets give none.
- [ ] Given a ledger tombstone and a row replanted in the answer cache, when the tombstone check runs, then `tombstone_violations_total` increments and the page metric fires.
- [ ] Given a request erased 25 h ago, then the tombstone check for it runs daily, not hourly (schedule test with a fake clock).
- [ ] Given a dataset with `max_time_travel_hours` 168, then the settings check pages.
