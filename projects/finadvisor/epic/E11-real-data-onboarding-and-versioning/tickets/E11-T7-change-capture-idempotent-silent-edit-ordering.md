---
key: "E11-T7"
title: "Change capture: idempotent observations, silent edit, ordering"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T5", "E11-T6"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "deep-dive/06-interfaces-and-contracts.md#6.7", "decision-logs.md#adr-26", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4 (#13)"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Record observations idempotently, detect silent edits and order by the source's version key.

## Description
Implement `record_observation()` and the version-creation step used by every connector, in one transaction per item.

Arch rules: idempotent on `(source_id, external_id, version_key, content_sha256)`; same bytes again is a no-op; **same `version_key` with new bytes is a `silent_edit` event: a new `document_versions` row with the same valid range and a new system range, the old row's `system_range` closed in the same transaction, and an alert**; order by the source's version key, never arrival time (a version older than the current head is accepted and left to `reconcile_lineage`); `observed_at` and system time from the DB clock. Cursor and `last_listing_at` on `source_registry` are updated in the same transaction as the observations they cover; every incremental read starts at `cursor - overlap_s` (default 48 h).

Emit the `silent_edit` event as a metric `source_silent_edit_total{source_id}` and a structured log; paging wiring is E9.

Out of scope: listing diff and withdrawal (E11-T8), lineage and chunks (E11-T9).

## Acceptance criteria
- [ ] Given the same observation fed twice then `source_observations` has one row and `document_versions` one row (test `test_observations.py::test_same_bytes_is_noop`).
- [ ] Given a fixture whose bytes are mutated under the same `version_key` then a new `document_versions` row exists with the same `valid_range`, the old row's `system_range` upper is set, and `source_silent_edit_total` is 1 (#13; test `test_silent_edit_creates_system_range_row`, PR).
- [ ] Given a failure inside the transaction after the observation insert then neither the observation nor the cursor change is committed (test `test_cursor_and_observations_atomic`).
- [ ] Given cursor T when `changes` is called then the request window starts at T minus 48 h (test `test_incremental_read_uses_overlap`).
