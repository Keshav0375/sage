---
key: "E13-T7"
title: "Cell down: 503 CELL_UNAVAILABLE; provider outage is not a cell failure"
epic: "E13"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E13-T6", "E4-T19"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.11", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4", "deep-dive/08-security-and-privacy.md#8.7", "decision-logs.md#adr-031", "decision-logs.md#adr-038"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 327, "id": 6263833383, "url": "https://github.com/Keshav0375/FinAdvisor/issues/327"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Stopping one cell fails only that cell's tenants with a clear 503, and an LLM outage is reported as `LLM_UNAVAILABLE` in every cell.

## Description
Implements: "Cell down: the router or ALB answers 503 `CELL_UNAVAILABLE` for that cell's tenants only; there is no cross-cell failover and no fallback to another cell. Provider outage in any cell returns `LLM_UNAVAILABLE`, not a cell failure (ADR-038)" (06 §6.11). Edge case #6: "compose: stop cell-eu: US passes, EU tenants get 503 with a clear code, no US data touched. Variant: provider outage returns `LLM_UNAVAILABLE` in every cell". In compose the router container answers (epic scope: compose router only).

Make the E13-T6 router return `503` with the standard envelope, code `CELL_UNAVAILABLE`, `retryable:true`, for requests to a cell whose upstream is down, never forwarding to another cell. Add `CELL_UNAVAILABLE` to the error-code map of E4-T4. Add a nightly-tagged test that stops `cell-eu` services; and a variant with the stub LLM set to fail in both cells asserting `LLM_UNAVAILABLE` and that the router/health metric `cell_up` stays 1 for both.

Out of scope: real ALB behaviour, Cloud Run, failover of any kind.

## Acceptance criteria
- [ ] Given `docker compose stop` of the `cell-eu` services, when `alpha` (us) chats, then it succeeds; when `beta` (eu) is called, then 503 `CELL_UNAVAILABLE` (`test_cell_down.py::test_stop_cell_eu`, #6, nightly).
- [ ] Given the same run, then the cell-us Postgres query log shows no statement for tenant `beta` and no request reached cell-us for `beta` (`test_cell_down.py::test_no_us_data_touched`).
- [ ] Given the stub LLM failing in both cells, when `alpha` and `beta` chat, then both get `LLM_UNAVAILABLE` and `cell_up` is 1 for both cells (`test_cell_down.py::test_provider_outage_not_cell_failure`, #6 variant).
- [ ] Given cell-eu stopped, then no request for `beta` is retried against cell-us (`test_cell_down.py::test_no_cross_cell_fallback`).
