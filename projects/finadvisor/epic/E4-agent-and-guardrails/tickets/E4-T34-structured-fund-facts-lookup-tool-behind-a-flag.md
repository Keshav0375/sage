---
key: "E4-T34"
title: "Structured fund-facts lookup tool over fund_rr_facts and KID fee rows"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T10", "E11-T10", "E11-T17", "E11-T21"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.3", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.9", "deep-dive/08-security-and-privacy.md#8.8", "deep-dive/02-quality-attributes.md#2.10", "decision-logs.md#adr-037", "decision-logs.md#adr-036"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 140, "id": 6263486781, "url": "https://github.com/Keshav0375/FinAdvisor/issues/140"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add a flagged tool `lookup_fund_facts` that answers fee and risk figures from structured rows instead of table chunks, so ablation arm 4 can be measured.

## Description
Confirmatory arm 4 of ADR-037 is "structured lookup (SEC RR facts, KID fee tables) vs table chunks". The default stays on table chunks; this tool is behind `STRUCTURED_LOOKUP_ENABLED` (default false; the ablation turns it on for its run, E7-T7). Implements a tool in the 6.3 style: Pydantic-validated input, `model_dump_json()` output, errors as `{"error_code"}`, no `tenant_id`, tier, jurisdiction or `as_of` argument (all from `Principal`).

`lookup_fund_facts(fund: string, fact?: enum)` returns `{results:[{fund_series, fact_name, value, unit, period, source: "sec_rr" | "kid", source_version_id, chunk_id}], total_found}`:
- `sec_rr` rows come from `fund_rr_facts` (PUBLIC, E11-T10; loaded by E11-T17), read through the same as-of and `valid_range` predicate as retrieval (5.9);
- `kid` rows come from `kid_fee_rows` (tenant-scoped, ENABLE + FORCE RLS, `fa_app` SELECT only), created by this ticket: `(tenant_id, id)`, `doc_id`, `version_id`, `cost_name`, `value`, `unit`, `source_chunk_id`. The rows are filled by a deterministic parser over the table chunks of KID versions (recognisable fee table, E11-T11 blocking rule; E11-T21 publisher KIDs), run by `scripts.fill_kid_fee_rows` for the eval tenant; a table the parser cannot read yields no rows (the question then falls back to chunk retrieval), never guessed values. The arch does not describe a stored KID fee structure; this table is the minimum needed for arm 4 (see the report's note).
Every returned figure carries `chunk_id` of the table chunk it came from, so the citation verifier and the numeric gate (8.6) compare against the original chunk text, and a licence footer is still produced for the source class. A role-policy row (8.8, default deny) is added; a tool without a row fails CI. A private-demo (`kid`) row is visible only to its firm tenant (RLS).

Out of scope: the ablation run (E7-T7), making the tool default-on, new connectors.

## Acceptance criteria
- [ ] Given `STRUCTURED_LOOKUP_ENABLED=false`, when the tool list is built, then `lookup_fund_facts` is absent and a call to it is rejected as an unknown tool (test `test_fund_facts.py::test_flag_off_hides_tool`).
- [ ] Given a fund with 2 `fund_rr_facts` rows, when the tool is called, then both come back with `source: sec_rr`, the value as stored and a `chunk_id`; a fund with no rows gives `total_found: 0` (test `test_fund_facts.py::test_rr_rows`).
- [ ] Given a KID table chunk with the row "Ongoing costs 0.45%", when `fill_kid_fee_rows` runs, then `kid_fee_rows` has `cost_name='Ongoing costs'`, value 0.45, unit `%` and `source_chunk_id` of that chunk; given an unreadable table, no rows are written (test `test_fund_facts.py::test_kid_parser_no_guess`).
- [ ] Given tenants A and B with their own KID rows, when A's advisor calls the tool, then only A's `kid` rows return (RLS) (test `test_fund_facts.py::test_kid_rows_tenant_isolated`).
- [ ] Given a returned figure, when the numeric gate runs on an answer that uses it, then it is grounded by the chunk text of `chunk_id`; an answer with a figure not in any returned row or cited chunk is withheld (test `test_fund_facts.py::test_numeric_gate_uses_chunk_text`).
- [ ] The role-policy matrix test fails if the policy row of `lookup_fund_facts` is removed.
