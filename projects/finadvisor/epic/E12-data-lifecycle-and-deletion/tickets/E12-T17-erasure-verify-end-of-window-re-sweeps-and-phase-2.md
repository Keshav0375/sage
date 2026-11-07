---
key: "E12-T17"
title: "erasure-verify: end-of-window re-sweeps and phase-2 receipt"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T16", "E12-T13", "E12-T14", "E12-T15", "E12-T12", "E12-T2"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "decision-logs.md#adr-30", "decision-logs.md#adr-29", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.11"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
After each store's window timer, re-sweep and probe the store, restart the clock on resurrection and sign the phase-2 receipt.

## Description
Job `erasure-verify` (runs while the system runs; the erasure job runs first at every demo start). For each `erasure_steps` row whose `window_closes_at` has passed and `swept_at` is null: re-run that store's delete and its probe (Postgres, GCS, BigQuery current rows plus the time-travel probe, Kafka topic scan, Langfuse GET, answer cache); if anything is found, delete it, record a resurrection event, restart that store's `window_closes_at` and leave `swept_at` null. When every store is swept clean, set the request `closed`, issue the phase-2 receipt (`windows_closed`, signed as in E12-T16) and update the ledger hash. BigQuery fail-safe, Cloud SQL PITR logs and provider retention are marked `documented` or `provider`, never `observed`. Out of scope: the hourly tombstone reconcile (E12-T23).

## Acceptance criteria
- [ ] Given a request with all windows elapsed and clean probes, when the job runs, then a phase-2 receipt is issued, status is `closed`, and the receipt marks BigQuery fail-safe as `documented`.
- [ ] Given a row replanted in Postgres after its window by a replayed message, when the job runs, then the row is deleted, the clock for that store restarts, and no phase-2 receipt is issued that pass (resurrection test).
- [ ] Given the Langfuse step unconfirmed, then no phase-2 receipt is issued.
- [ ] Given a phase-2 receipt, then it is issued once only (idempotent rerun) and contains the phrase 'windows closed' and the per-store window kinds.
