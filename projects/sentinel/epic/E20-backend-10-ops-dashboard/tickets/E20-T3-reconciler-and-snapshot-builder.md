---
key: "E20-T3"
title: "Reconciler and snapshot builder"
epic: "E20"
repo: "Sentinel"
size: "M"
status: "done"
depends_on: ["E20-T1"]
arch_refs: ["deep-dive/11-observability-and-ops-dashboard.md#11.3"]
issue: null
branch: "dev/backend-phase-10-ops-dashboard"
pr: "https://github.com/Keshav0375/Sentinel/pull/33"
updated: "2026-11-08"
---

## Summary
`ops_reconcile.yml` (every 30 min, on `workflow_run`, manual) pulls runs, PRs, reviews and merges of both repos read-only, plus Langfuse trace summaries (names and timings only), appends missing events and rebuilds `snapshot/`.

## Description
Source: backend task 10.3 (built in https://github.com/Keshav0375/Sentinel/pull/33).

`ops_reconcile.yml` (every 30 min, on `workflow_run`, manual) pulls runs, PRs, reviews and merges of both repos read-only, plus Langfuse trace summaries (names and timings only), appends missing events and rebuilds `snapshot/`.

## Acceptance criteria
- [x] Re-running the reconciler adds no duplicate events
- [x] Snapshots carry `generated_at` and the ledger head sha
- [x] Trace summaries contain no inputs or outputs

## Outcome
Merged in https://github.com/Keshav0375/Sentinel/pull/33 on 2026-10-28.
