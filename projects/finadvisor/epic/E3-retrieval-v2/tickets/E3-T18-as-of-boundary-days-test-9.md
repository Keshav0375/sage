---
key: "E3-T18"
title: "As-of boundary-day test (#9) for retrieve"
epic: "E3"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E3-T9"]
arch_refs: ["decision-logs.md#adr-027", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.6"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Prove that retrieval returns the same chunks on boundary days, with the app clock shifted two hours either way and on a DST day.

## Description
Edge case #9 (deep-dive/07 section 7.4, tier PR; plan E3 Done when, Round 4): "boundary days: `valid_from`, `valid_to`, day before and after; app clock +/-2 h and the DST day; same chunks returned". ADR-027: `as_of` comes from the resolver or the Postgres date in UTC, never the model; ranges are half-open.

Add `backend/tests/test_as_of_boundaries.py` (marked `integration`, runs in the PR gate) on a fixture with one provision in two versions: v1 valid `[2020-01-01, 2021-01-01)`, v2 valid `[2021-01-01, ∞)`, with `search` and `retrieve` stubbed for Voyage. Cases:
1. `as_of` = `valid_from` of v1, the last day of v1 (2020-12-31), `valid_to`/`valid_from` boundary (2021-01-01), the day before v1 (2019-12-31) and the day after the boundary (2021-01-02): assert the exact chunk ids expected (v1, v1, v2, none, v2).
2. For each of those dates the date is produced by the injectable UTC clock (E3-T8) at 12:00 UTC shifted by -2 h and +2 h: the same chunk ids come back for both shifts.
3. The DST days 2026-03-29 (Europe/London) and 2026-03-08 (America/New_York) and the end-of-DST days 2026-10-25 and 2026-11-01 used as `as_of` and as the clock date give the same chunk ids as the neighbouring days that share a version.

Out of scope: the date parser and UI chip (E4-T18), the answer echo.

## Acceptance criteria
- [ ] Given the fixture, when `search` runs for each boundary date in case 1, then the returned chunk ids equal the expected ids (v1, v1, v2, none, v2) (`test_as_of_boundaries.py::test_boundary_days`).
- [ ] Given the clock shifted -2 h and +2 h around 12:00 UTC on each date in case 1, then the chunk ids equal those of the unshifted clock (`test_clock_shift_same_chunks`).
- [ ] Given each DST date in case 3, then the chunk ids equal those of the day before and the day after when they share a version (`test_dst_days_same_chunks`).
- [ ] Given the half-open predicate mutated to `valid_range && daterange($5, $5, '[]')` in a scratch copy of the statement, then `test_boundary_days` fails at the 2021-01-01 case (mutation check proves the test can fail).
