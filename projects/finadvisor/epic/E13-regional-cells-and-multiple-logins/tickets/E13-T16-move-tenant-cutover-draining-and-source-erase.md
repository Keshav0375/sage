---
key: "E13-T16"
title: "move-tenant: cutover, moved 421, grace and source erase"
epic: "E13"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E13-T15", "E13-T4", "E13-T2", "E12-T8", "E12-T16"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.6", "decision-logs.md#adr-033", "decision-logs.md#adr-029"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
After a verified copy the job publishes a new signed `cells.json`, the source answers 421 `TENANT_MOVED`, and after the grace the source tenant is erased with a receipt.

## Description
Implements ADR-033: "Cutover: publish a new signed `cells.json` atomically. The source tenant becomes `moved` (421) and is erased after a 7-day grace through ADR-029 with a receipt." Depends on E12 (erasure worker and receipts; exact ticket keys to be set).

`cutover`: build the next `cells.json` (version + 1, the tenant's `home_cell` set to the target, `state` per 06 §6.11), sign it (E13-T1 CLI/library, key from the operator), and publish with one atomic object write to the GCS location (compose router file replace); both cells then apply it within `CELLS_REFRESH_S`. The source tenant row `cell_id`/state becomes `moved`; E13-T4 answers `TENANT_MOVED` with the target hint. `draining`: set `grace_until = now + MOVE_GRACE_DAYS` (default 7, config value). At `grace_until` the job enqueues a tenant erasure request through the ADR-029 `deletion_requests` flow of E12 for the source tenant's data and waits for the receipt; then state `source_erased`. The tenant row on the target is `active`. A failure before `cutover` follows E13-T13 rollback; after `cutover` there is no rollback.

Out of scope: erasure internals (E12), Langfuse trace move (does not move).

## Acceptance criteria
- [ ] Given a verified copy, when `cutover` runs, then `cells.json` version increments, its signature verifies, and after one refresh interval both cells resolve the tenant to the target cell (`test_move_cutover.py::test_publish_and_resolve`).
- [ ] Given cutover done, when the tenant is called on the source cell, then 421 `TENANT_MOVED` with the target hint and zero DB reads; on the target it answers normally with the same data (`test_move_cutover.py::test_source_moved_target_serves`).
- [ ] Given `MOVE_GRACE_DAYS` shortened to a few seconds in test, when the grace passes, then the source erasure runs, the source holds zero rows for the tenant, and an erasure receipt exists; state is `source_erased` (`test_move_erase.py::test_erase_after_grace_with_receipt`).
- [ ] Given a failure injected after cutover, then the job does not roll back and the directory still points to the target (`test_move_cutover.py::test_no_rollback_after_cutover`).
