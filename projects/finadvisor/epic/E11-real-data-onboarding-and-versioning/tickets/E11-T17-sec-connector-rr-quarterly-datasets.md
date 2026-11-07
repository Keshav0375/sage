---
key: "E11-T17"
title: "sec connector: RR quarterly datasets into fund_rr_facts"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T10", "E11-T6", "E11-T7"]
arch_refs: ["deep-dive/11-tech-stack.md#source-connectors-r4", "deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.11", "decision-logs.md#adr-26"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Load the SEC Risk/Return quarterly datasets into the structured fund_rr_facts table.

## Description
Implement the RR half of `sec` (PUBLIC, structured facts, `source_class=law`, retire; "a structured cross-check, not a substitute for filings").

Arch: quarterly zip of text and numeric files (about 97 KB to about 78 MB, 82 MB cited in 6.7); no key; same SEC site limits and declared User-Agent; lag about 2 weeks; facts go to `fund_rr_facts`, not chunks. `version_key` = the quarter file id. The fact columns are the ones set in E11-T10 (this ticket does not change the table). Writer role `fa_etl_public`; stream the zip, do not load it fully into memory.

Out of scope: any use of the facts by the agent tools (E3/E4); 497K (E11-T16).

## Acceptance criteria
- [ ] Given the recorded small quarter zip then rows are inserted into `fund_rr_facts` with `tenant_id = PUBLIC` and the row count equals the numeric file's row count (test `backend/tests/connectors/test_sec_rr.py::test_quarter_loads_expected_rows`).
- [ ] Given the same quarter loaded twice then no duplicate rows and one observation (test `test_quarter_reload_idempotent`).
- [ ] Given an 82 MB synthetic zip then peak memory stays under the configured cap (`SEC_RR_MAX_RSS_MB`, test `test_large_zip_streams`).
- [ ] Given a quarter file removed from the listing twice then the facts are retired (valid range closed), not deleted (test `test_rr_withdrawal_retires`).
