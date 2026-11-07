---
key: "E13-T4"
title: "principal: WRONG_CELL and TENANT_MOVED 421, zero DB reads"
epic: "E13"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E13-T2", "E1-T14", "E4-T4"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.11", "deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4", "decision-logs.md#adr-031"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
A request for a tenant homed in another cell, or a moved tenant, gets 421 with a cell hint before any database read.

## Description
Implements: "`principal` (§4.5) checks `home_cell == this cell` and returns before any database read: HTTP 421 with `{"error": {"code": "WRONG_CELL", "message", "request_id", "retryable": false}, "cell_hint": {"cell_id", "api_endpoint"}}`. A tenant whose `state` is `moved` gets 421 `TENANT_MOVED` with the new cell hint. Code names are proposed here and fixed in E13" (06 §6.11); edge case #16.

Extend the E1 `principal` dependency: after token verification and before the entitlement cache load or any `SET LOCAL` or query, resolve the URL tenant through `CellDirectory` and compare `home_cell` with `HOME_CELL`. Mismatch: `WRONG_CELL` 421 with the real home cell as `cell_hint`. `state == moved`: `TENANT_MOVED` 421 with the new cell hint. Add both codes (421, `retryable:false`) to the stable error-code map of E4-T4. A tenant absent from the directory stays `UNAUTHENTICATED`. Reuse the query-log fixture of the E1 leak matrix for the test.

Out of scope: the token versus URL check (E13-T5), 503 cell-down (E13-T7), SPA handling of 421 (E8-T4).

## Acceptance criteria
- [ ] Given cell-us and a valid token for a tenant homed in `eu`, when `GET /v1/conversations` is called, then 421 `WRONG_CELL` with `cell_hint.cell_id == "eu"` and an empty Postgres query log for the request (`test_wrong_cell.py::test_421_zero_db_reads`, #16).
- [ ] Given a tenant with `state: moved` to `eu`, when called on the source cell, then 421 `TENANT_MOVED` with the `eu` hint and zero DB reads (`test_wrong_cell.py::test_moved`).
- [ ] Given a correct-cell request, then behaviour is unchanged and the E1 leak matrix passes (`pytest -m l0_leak`).
- [ ] The 421 body matches the 06 §6.11 shape including `request_id` and `retryable:false` (`test_wrong_cell.py::test_body_shape`).
