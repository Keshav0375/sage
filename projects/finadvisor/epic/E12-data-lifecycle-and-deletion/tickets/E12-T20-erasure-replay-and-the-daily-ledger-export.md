---
key: "E12-T20"
title: "erasure-replay and the daily ledger export"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T8"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "decision-logs.md#adr-29", "decision-logs.md#adr-30", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#14"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Export the ledger daily to an append-only GCS object and re-apply it after any restore before traffic.

## Description
Implement `ledger-export` (daily while the system runs): write the `erasure_ledger` rows to a new GCS object per day under an append-only bucket policy (object versioning off, writes only, no overwrite: use a unique name per run), recording the object hash. Implement `erasure-replay` (command and job): after ANY restore (backup, PITR, move target) it reads the Postgres ledger, then every export object, and re-applies each tombstone through the same single-document erase path (E12-T8..T10), so entries newer than the restored backup are still replayed; it exits non-zero while any tombstone is unapplied, and readiness (E0-T5) refuses traffic until it exits zero (a flag row `restore_replay_required` set by the restore runbook step). Out of scope: the cloud restore runbook, move-tenant replay (E13).

## Acceptance criteria
- [ ] Given a backup taken before an erasure and restored into scratch Postgres, when `erasure-replay` runs, then the erased document's chunk, version and document counts are 0 (#14; compose, nightly).
- [ ] Given a ledger entry newer than the backup that exists only in the GCS export, when replay runs, then it is applied (export-only entry test).
- [ ] Given `restore_replay_required` is set, when `/readyz` is called before replay completes, then it is not ready; after replay it is ready.
- [ ] Given two ledger-export runs on the same day, then two distinct objects exist and none is overwritten.
