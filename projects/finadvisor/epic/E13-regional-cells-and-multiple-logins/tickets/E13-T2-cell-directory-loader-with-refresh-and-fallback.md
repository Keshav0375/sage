---
key: "E13-T2"
title: "CellDirectory loader: GCS read, 60 s refresh, baked fallback"
epic: "E13"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E13-T1"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.11", "deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "decision-logs.md#adr-031"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Each service reads the signed directory at start, refreshes it every 60 s, and survives an unreadable or tampered file.

## Description
Implements: "a signed static `cells.json` ... kept in GCS with a baked fallback, read at start and refreshed every 60 s; no control-plane database" (deep-dive/04-2 §4.24) and "Unreadable or badly signed file: the last good copy, then the baked fallback" (06 §6.11).

Build `backend/app/cells/directory.py`: `CellDirectory` with `load()` at start, a background refresh every `CELLS_REFRESH_S` (60), and lookups `by_slug`, `by_tenant_id`, `by_idp_tenant`, `this_cell()` (from `HOME_CELL`), `endpoint(cell_id)`. Sources behind a `CellsSource` interface: `GcsSource(CELLS_JSON_URI)` and `FileSource` (compose, where the router serves the file). Per refresh: fetch, verify signature, require `version` greater than the held version, swap atomically; on read error or bad signature keep the last good copy; at start with nothing readable use the baked fallback (E13-T1). Never apply an older version. Metrics `cells_refresh_total{result=ok|stale|bad_signature|unreadable}` and gauge `cells_version`.

Out of scope: 421 logic (E13-T4), `/resolve` (E13-T3), publishing a new file (E13-T16).

## Acceptance criteria
- [ ] Given a valid v43 file in the source, when the refresh runs, then lookups return v43 data and `cells_version` is 43 (`test_directory.py::test_refresh_applies_newer`).
- [ ] Given the source becomes unreadable after v43 loaded, when the refresh runs, then lookups still return v43 data and `result=unreadable` increments (`test_directory.py::test_last_good_copy`).
- [ ] Given the source is unreadable at start, when `load()` runs, then the baked fallback is used (`test_directory.py::test_baked_fallback_at_start`).
- [ ] Given a v44 file with a tampered signature, then it is rejected, v43 stays and `result=bad_signature` increments; a validly signed v42 is also not applied (`test_directory.py::test_tampered_and_stale_rejected`).
