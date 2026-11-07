---
key: "E12"
title: "Data lifecycle and deletion"
phase: 3
phase_name: "Real data and lifecycle"
repo: "FinAdvisor"
status: "todo"
depends_on: ["E11", "E5", "E6", "E1"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.17", "deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "deep-dive/04-2-source-lifecycle-and-cells.md#4.20", "deep-dive/04-2-source-lifecycle-and-cells.md#4.22", "deep-dive/04-2-source-lifecycle-and-cells.md#4.23", "deep-dive/04-2-source-lifecycle-and-cells.md#4.27", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.11", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.12", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.13", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.14", "deep-dive/06-interfaces-and-contracts.md#6.9", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4", "deep-dive/09-observability.md#9.7", "deep-dive/09-observability.md#9.8", "decision-logs.md#adr-028", "decision-logs.md#adr-029", "decision-logs.md#adr-030", "decision-logs.md#adr-034", "decision-logs.md#adr-035", "decision-logs.md#adr-039"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 116, "id": 6263449381, "url": "https://github.com/Keshav0375/FinAdvisor/issues/116"}
updated: "2026-11-07"
---

## Goal
A delete is a physical delete on every live store within the stated windows, proven by receipts and a canary; drift between stores is detected hourly; an embedding-model change cannot mix generations. Includes reconciliation and the canary.

## Scope
Tickets E12-T1 to E12-T28 (12 S, 16 M). Spikes first (T1 to T4).
- Spikes: Cloud SQL backup expiry while stopped (T1), BigQuery probe (T2), Langfuse delete stub (T3), Voyage throughput under the 25% cap (T4).
- Tables: deletion queue, steps, receipts, ledger (T5); `source_purges`, reconciliation manifests and findings (T6).
- Queue and worker: `erasure-worker` with SKIP LOCKED (T7); tombstone first under the per-document lock, operator `release`, legal hold (T8); admin API (T11).
- Per-store steps: Postgres ordered DELETE, VACUUM, cache purge (T9); advisor scope and `pseudonym_id` unlink (T10); GCS (T12); BigQuery batched DML (T13); Kafka wait and scan (T14); Langfuse retry and 24 h alert (T15).
- Proof: phase-1 receipt signed with the KMS HMAC key (T16); `erasure-verify` re-sweeps and phase-2 receipt (T17); promise wording (T18).
- Pull-model `purge_source` (T19, R4-D19 M6); `erasure-replay` and daily ledger export (T20); canary drill at demo start (T21).
- Reconciliation: hourly `reconcile` pairs (T22, T23); replay-twice test (T24).
- Embedding generations: schema and wrong-model guard (T25); `embed-backfill` with dual write (T26); validation and per-tenant flip (T27); retire after 7 d (T28).
- E12 owns `source_purges`, `erasure_receipts`, `reconciliation_manifests`, `reconciliation_findings` (plan); this epic also creates `deletion_requests`, `erasure_steps` and `erasure_ledger`. The cell-versus-cell PUBLIC manifest pair is E13.

## ADRs
ADR-028 (atomic publish, tombstones, lock order), ADR-029 (erasure architecture, store windows), ADR-030 (receipts, canary, tombstone invariant), ADR-034 (reconciliation), ADR-035 (embedding generations), ADR-039 (amendments: pull-model purge, BigQuery default via `ALTER PROJECT`, PITR 7 d, spike V5).

## Exit criteria
Edge-case catalogue ids in brackets.
- N interleavings of erase vs indexer with the real worker, including a tombstone committed immediately before the sink write, end with zero rows and objects and `tombstone_violations_total` = 0 (#1; PR). Two concurrent multi-document erasures plus an ingest storm: no deadlock loss, lock order held (#29). (T8, T23)
- Erasing a document from firm A leaves firm B untouched; A's cache and BigQuery are purged (#4; PR). (T9, T13)
- With Kafka stopped, an erasure completes its Postgres steps and leaves the others pending; after restart all finish and phase 1 is issued once (#7; PR). (T14, T16)
- Restoring a pre-erasure backup into scratch and running `erasure-replay` gives counts 0 (#14). (T20)
- `purge_source` on fixtures with the per-firm pull empties every store for the source, issues a receipt and purges cached answers quoting FCA text (#15; drilled quarterly). (T19)
- A half-built generation keeps queries on blue; the flip moves them to green; a wrong-model query raises (#19). Erasing during a backfill leaves zero rows in both generations and a receipt (#20). (T25 to T27)
- Erasing a subject within 5 min of events removes the rows on the next BigQuery batch (#23). A Langfuse stub that returns 202 without deleting fires the 24 h alert and the receipt stays phase 1 (#24). (T13, T15)
- Replaying the fixture corpus twice after a parser bump gives the single-run hash with zero resurrection (#8). (T24)
- Reconcile on fixtures passes for each pair and detects a planted difference; the ANN canary pages on a deliberately broken index (#28). (T22, T23)
- The canary drill records the time to zero for each observable store. (T21)
- Spike results recorded: backup expiry while stopped, BigQuery probe, Langfuse delete shape, Voyage throughput. (T1 to T4)

## Questions
Resolved by R4-D20 (applied): E11 tickets exist (keys managed by the orchestrator); `erasure_ledger` is created in E12-T5; the uncached sink-guard helper is a new E5 ticket (key to follow); `pseudonym_map` is an E1 ticket (key to follow); canary results as a GCS JSON object accepted; Terraform, KMS and the export bucket are E10, alert policies E9; a store not at zero inside its window is a failed canary (T21). Config keys `ERASURE_MAX_ATTEMPTS` and `EMBED_BLUE_KEEP_DAYS` go into 6.6 in a later arch pass.
Open: none.
