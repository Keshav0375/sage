---
key: "E13-T15"
title: "move-tenant: GCS and BigQuery copy, kill-target test"
epic: "E13"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E13-T14", "E6-T17"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.6", "decision-logs.md#adr-033"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 320, "id": 6263825543, "url": "https://github.com/Keshav0375/FinAdvisor/issues/320"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
The tenant's GCS prefix and BigQuery rows are copied to the target cell, and killing the target mid-copy leaves the source intact and the target empty.

## Description
Implements ADR-033: "GCS prefix copy, BigQuery export and load" and edge case #18: "kill the target mid-copy: source intact and unfrozen, target empty; success path counts and hashes equal".

Extend `copying`/`verifying` (E13-T13, E13-T14): copy the tenant's GCS prefix (object count and sha256 per object compared) and export the tenant's BigQuery rows (the E6-T17 partitioned tables) to the target dataset, then load; verify row counts and an md5 over ordered event ids per table. Compose uses the fake GCS and the BigQuery emulator or stub already used by E6; the BigQuery location is per cell and no cross-location join is used (export then load only). Langfuse traces do not move: the job logs this and does not touch Langfuse. Rollback (E13-T13) additionally deletes the target GCS prefix and target BigQuery rows for the tenant.

Out of scope: cutover and erase (E13-T16).

## Acceptance criteria
- [ ] Given a seeded tenant, when the move completes `verifying`, then GCS object counts and sha256s and BigQuery counts and md5s are equal on both sides (`test_move_stores.py::test_gcs_and_bq_equal`).
- [ ] Given the target Postgres container is killed mid-`copying`, when the job fails, then the source tenant is unfrozen and its row counts are unchanged, and the target holds zero rows, no GCS objects and no BigQuery rows for the tenant (`test_move_kill_target.py::test_kill_target_mid_copy`, #18, nightly).
- [ ] Given a corrupted target GCS object, then `verifying` fails and rollback removes the prefix (`test_move_stores.py::test_gcs_corruption_detected`).
- [ ] Given a completed copy, then no Langfuse call was made by the job (`test_move_stores.py::test_langfuse_not_moved`).
