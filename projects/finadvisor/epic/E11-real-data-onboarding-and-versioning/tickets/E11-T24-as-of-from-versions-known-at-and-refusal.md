---
key: "E11-T24"
title: "As-of from versions: known_at and no-history refusal"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T9", "E11-T7", "E3-T5", "E4-T18"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.18", "deep-dive/06-interfaces-and-contracts.md#6.10", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.9", "decision-logs.md#adr-27", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4 (#9, #13, #25)"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 274, "id": 6263723098, "url": "https://github.com/Keshav0375/FinAdvisor/issues/274"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Answer as-of questions from versions, reproduce past answers by known_at and refuse UK dates before observation.

## Description
Verify and complete the as-of path on real versions. Arch (4.18, 6.10): the retrieval SQL filters `valid_range @> $as_of::date AND upper_inf(system_range)`; a CI test requires the predicate in every SQL string of the retrieval module; a second check after generation blocks any cited chunk whose `valid_range` does not contain `as_of` (also on a cache hit). `known_at` queries exist for admin, audit and eval only; older beliefs are closed, never overwritten. UK sources (`valid_from_basis='observed'`) refuse a date before the first observation: `refusal {code: "ANSWER_WITHHELD", reason: "no_version_history"}` with the text "no version history for this source". The resolver (E4) is used as is; this ticket adds the `known_at` helper (`retrieval.search_known_at`, not exposed to the model or public API) and the end-to-end tests. `as_of` and `known_at` boundaries: half-open `[from, to)`, UTC days from the DB date.

Date-format rule (R4-D20): ISO 8601 is always accepted; numeric DD/MM vs MM/DD follows the advisor's jurisdiction (US month-first, EU/UK day-first); the parsed date is echoed in the answer.

## Acceptance criteria
- [ ] Given an FCA question as of 2019 (before the first observation) then the response is `ANSWER_WITHHELD` with reason `no_version_history` and zero model calls (#25; test `backend/tests/integration/test_as_of.py::test_fca_2019_refused_no_version_history`, PR).
- [ ] Given a version superseded by a silent edit when `search_known_at` is called with a `known_at` before the edit then the old text is returned and with a later `known_at` the new text (#13; test `test_known_at_reproduces_past_answer`, PR).
- [ ] Given boundary days (valid_from, valid_to, day before and after), app clock +/- 2 h and a DST day then the same chunks are returned (#9; test `test_as_of_boundaries_and_clock_skew`, PR).
- [ ] Given a cited chunk whose `valid_range` does not contain `as_of` then the release is blocked, also on a cache hit (test `test_post_generation_valid_range_check`).
- [ ] Given a retrieval SQL string without the `valid_range @>` predicate then the CI check fails (test `test_every_retrieval_sql_has_as_of_predicate`).
- [ ] Given the question date `03/04/2024` then a US advisor gets 2024-03-04 and a UK advisor gets 2024-04-03, ISO 8601 `2024-04-03` parses the same for both, and the answer echoes the parsed date (tests `test_as_of.py::test_ambiguous_date_us_advisor`, `test_ambiguous_date_uk_advisor`, `test_iso_always_accepted`).
