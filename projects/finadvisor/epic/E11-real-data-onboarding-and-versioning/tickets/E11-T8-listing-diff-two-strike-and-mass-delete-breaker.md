---
key: "E11-T8"
title: "Listing diff: two-strike withdrawal and mass-delete breaker"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T7"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "deep-dive/06-interfaces-and-contracts.md#6.7", "decision-logs.md#adr-26", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4 (#12)"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Apply withdrawals only after two complete listings and freeze the connector on a suspicious drop.

## Description
Implement `apply_listing(source_id, listing)` run by the connector runner after each full `list()`.

Arch: "Feeds only accelerate; the full-listing diff is the truth for deletes." An item is withdrawn only after two consecutive complete listings omit it (state `withdrawn`, read from the last two complete `listing_run_id`s). Mass-delete breaker: a listing that drops more than 5 items or more than 10% of a source applies nothing, sets `source_registry.frozen` with `frozen_reason`, and raises a page (metric `source_frozen{source_id,reason}`; alert rule wiring is E9); **a listing with 0 items is always a failure** (same freeze). An unfreeze is an explicit operator action that records who and when. Also freeze on a contract-failure rate (E11-T12) and on 401 or 403 (E11-T22), using the same column.

Out of scope: what a withdrawal does to the data (retire or erase, E11-T10).

## Acceptance criteria
- [ ] Given an item missing from one listing then no withdrawal is applied; missing from a second consecutive complete listing then state `withdrawn` is recorded (test `test_listing_diff.py::test_two_strike_withdrawal`).
- [ ] Given a listing with 0 items then nothing is applied, `frozen` is true and the page metric is incremented (#12; test `test_empty_listing_freezes`, PR).
- [ ] Given a listing that drops 30% of a source (and separately 6 items of 100) then nothing is applied and the connector is frozen; a drop of exactly 5 items of 100 is applied (#12; tests `test_mass_delete_breaker_percent`, `test_breaker_item_threshold_boundary`, PR).
- [ ] Given a frozen connector when the runner starts then it does not call `fetch` until an operator unfreeze is recorded (test `test_frozen_connector_does_not_run`).
