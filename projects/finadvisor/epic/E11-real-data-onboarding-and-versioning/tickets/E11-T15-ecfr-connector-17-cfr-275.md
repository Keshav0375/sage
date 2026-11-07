---
key: "E11-T15"
title: "ecfr connector: 17 CFR 275 versions"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T3", "E11-T6", "E11-T7", "E11-T9"]
arch_refs: ["deep-dive/11-tech-stack.md#source-connectors-r4", "deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "deep-dive/06-interfaces-and-contracts.md#6.7", "decision-logs.md#adr-26"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Implement the eCFR connector with gzip, 1 rps and point-in-time versions.

## Description
Implement `ecfr` (target PUBLIC, class `law`, on withdraw retire) in `backend/src/connectors/ecfr.py`.

Arch (6.7 and Source connectors): REST versioner API, no key; must send `Accept-Encoding: gzip` (else 406); <= 1 rps (set from E11-T3); incremental: `titles.json` `up_to_date_as_of` advances, then diff `versions/title-17.json?part=275` on `(identifier, amendment_date, issue_date)`; `removed: true` = retire; `substantive: false` = metadata only; point-in-time `/full/{date}/` XML per version; labelled non-authentic (`attribution_text`); `licence_class=us_gov`; daily cadence. `version_key` = `amendment_date` plus `issue_date` identifier; `valid_from` = amendment date, `valid_from_basis='source'`.

Out of scope: parsing to chunks (E6 silver), FCA or other sources.

## Acceptance criteria
- [ ] Given the recorded fixture for part 275 then `list()` returns the section set and `classify()` returns jurisdiction US, `licence_class=us_gov`, non-null `attribution_text` that says non-authentic (test `backend/tests/connectors/test_ecfr.py::test_list_and_classify_fixture`).
- [ ] Given every request made then it carries `Accept-Encoding: gzip` and the rate does not exceed 1 rps (test `test_gzip_header_and_throttle`).
- [ ] Given a version record with `removed: true` then an observation with state `withdrawn` candidate is produced and the retire policy is applied after two listings (test `test_removed_true_is_retire_after_two_strikes`).
- [ ] Given `up_to_date_as_of` has not advanced then no version fetch is made (test `test_no_change_no_fetch`).
- [ ] The connector passes the recorded-fixture suite in the PR gate; the `live` smoke case is registered for the weekly run (test marker check `test_live_smoke_registered`).
