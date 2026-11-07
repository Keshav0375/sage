---
key: "E13-T13"
title: "move-tenant job: state machine, freeze and rollback"
epic: "E13"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E13-T2", "E5-T10", "E4-T21"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.6", "decision-logs.md#adr-033"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
The `move-tenant` job moves through the ADR-033 states, freezes the source tenant, and rolls back on any failure before cutover.

## Description
Implements ADR-033: "States `active -> freezing -> copying -> verifying -> cutover -> draining -> source_erased`. Freeze: chat disabled for the tenant and the outbox drained to 0 ... Failure before cutover: unfreeze the source, delete partial target rows." State storage: a `tenant_moves` table in the source cell DB, owned by E13, set in E13-T13 per orchestrator.

Add migration `tenant_moves(id, tenant_id, source_cell, target_cell, state, started_at, updated_at, error, grace_until)` (state check constraint on the seven states; no RLS-exposed access for `fa_app`, written only by the job role). Add `backend/app/jobs/move_tenant.py` with `move-tenant --slug --to <cell>` implementing the state transitions as idempotent steps, resumable by state. `freezing`: set a tenant flag so chat returns a clear refusal (reuse the `tenants` kill flag of E1/E4 if present), wait until no `outbox` rows for the tenant are unpublished (relay from E5-T10), then record counts. `copying`/`verifying` are stubs here, filled by E13-T14 and E13-T15; `cutover` onward by E13-T16. `rollback()` for any failure before `cutover`: unfreeze source, delete the target's partial rows for the tenant (target tenant-scoped tables in reverse order), set state back to `active` with `error`.

Out of scope: copy and verify logic, cutover, erase.

## Acceptance criteria
- [ ] Given the `tenant_moves` table, when a row with an invalid state is inserted, then the constraint rejects it (`test_move_state.py::test_state_constraint`).
- [ ] Given a started move, when `freezing` runs, then a chat request for the tenant is refused with a clear code and the job waits until the tenant's unpublished outbox count is 0 (`test_move_freeze.py::test_freeze_drains_outbox`).
- [ ] Given a failure injected in `copying`, when the job handles it, then the source is unfrozen, the target holds zero rows for the tenant, and the state is `active` (`test_move_rollback.py::test_rollback_before_cutover`).
- [ ] Given the job is killed in `freezing` and restarted, then it resumes without a second freeze or duplicate row (`test_move_state.py::test_resume_idempotent`).
