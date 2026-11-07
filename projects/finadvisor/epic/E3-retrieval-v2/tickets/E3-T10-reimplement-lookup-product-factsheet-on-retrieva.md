---
key: "E3-T10"
title: "Reimplement lookup_product_factsheet on RetrievalService"
epic: "E3"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E3-T8"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.3", "deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#adr-004"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 70, "id": 6155653271, "url": "https://github.com/Keshav0375/FinAdvisor/issues/70"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Move the factsheet tool onto RetrievalService with escaped input, a LIMIT, and redacted chunks only.

## Description
Add `RetrievalService.factsheet(product_name) -> FactsheetResult` and rewrite `backend/src/agent/tools/lookup_factsheet.py` to call it. The tool no longer issues SQL.

Arch (§6.3): `lookup_product_factsheet`, input `product_name: string` ("wildcards escaped, `LIMIT` enforced"), output `{results:[{title, jurisdiction, regulatory_ref, last_reviewed_at, product_category, risk_level, stale, chunks:[redacted text]}], total_found}`, "redacted chunks only; no `raw_content` (G-03)". §5.2: "The factsheet tool returns document metadata plus up to `FACTSHEET_MAX_CHUNKS` redacted parent chunks through `retrieval.factsheet`, never raw content." Config: `FACTSHEET_MAX_CHUNKS` (required; value set in E4: read it from Settings, tests use a fixture value).

Behaviour: match `documents.title` / `product_category` with a parameterized ILIKE where `%`, `_` and the escape character in `product_name` are escaped (use `ESCAPE '\'`); hard `LIMIT` on documents (a named constant) and `FACTSHEET_MAX_CHUNKS` parent chunks per document; only documents with `status='active'`; staleness through `is_stale` (E3-T8); tenant / tier / jurisdiction come from RLS only. Pydantic input model with `extra='forbid'` and a max length; the tool takes no tenant, tier or jurisdiction argument; errors return `{"error_code"}`. Selected columns never include a `raw_content` column (which no longer exists after E1).

Out of scope: choosing the value of `FACTSHEET_MAX_CHUNKS` (E4), suitability (E3-T11).

## Acceptance criteria
- [ ] Given `product_name='%'` when the tool runs then it matches only documents whose title literally contains '%' (none in the fixture) and returns `total_found=0` (test `backend/tests/test_lookup_factsheet.py::test_wildcards_escaped`).
- [ ] Given 50 matching documents when the tool runs then at most the LIMIT constant documents are returned and each has at most `FACTSHEET_MAX_CHUNKS` chunks (test `test_limits_enforced`).
- [ ] Given a document with `tier_required` above the principal's tier when the tool runs then it is absent (test `test_factsheet_respects_rls`).
- [ ] Given the tool is called with `tenant_id` as an argument then `{"error_code"}` is returned (test `test_tool_rejects_tenant_argument`).
- [ ] A SQL-text scan test asserts the factsheet query string contains neither `raw_content` nor string interpolation of `product_name` (test `test_no_raw_content_no_interpolation`).
