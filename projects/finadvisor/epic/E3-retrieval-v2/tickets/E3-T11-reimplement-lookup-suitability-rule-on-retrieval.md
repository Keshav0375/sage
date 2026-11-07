---
key: "E3-T11"
title: "Reimplement lookup_suitability_rule on RetrievalService"
epic: "E3"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E3-T5"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.3", "deep-dive/05-data-model-and-storage.md#5.2", "decision-logs.md#adr-004"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 71, "id": 6155654464, "url": "https://github.com/Keshav0375/FinAdvisor/issues/71"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Move the suitability tool onto RetrievalService with typed inputs, a LIMIT and staleness.

## Description
Add `RetrievalService.suitability(product_category, client_risk_profile) -> SuitabilityResult` and rewrite `backend/src/agent/tools/lookup_suitability.py` to call it.

Arch (§6.3): `lookup_suitability_rule`, input `product_category: string`, `client_risk_profile: enum(conservative, moderate, aggressive)`, output `{rules:[{rule_name, product_category, client_risk_profile, jurisdiction, regulatory_ref, rule_text, last_reviewed_at, stale}], total_found}`; "reads `suitability_rules`, populated by the ETL (G-07)". §5.2 `suitability_rules`: `rule_name`, `product_category`, `client_risk_profile` CHECK 3 values, `min_tier_required`, `jurisdiction`, `regulatory_ref`, `rule_text` (redacted), `last_reviewed_at`. ADR-004 / the epic scope: "factsheet and suitability tools reimplemented on `RetrievalService` (no `raw_content`, escaped input, `LIMIT`)".

Behaviour: parameterized query on `suitability_rules` (exact or escaped-ILIKE match on `product_category` - use the same escaping helper as E3-T10, extracted to `retrieval/sql_utils.py` if not yet shared), `client_risk_profile` validated by the enum, hard `LIMIT` constant, `stale` via `is_stale`; access filtering by RLS (own tenant plus PUBLIC, tier and jurisdiction), no WHERE on `min_tier_required` in application code. Pydantic input model `extra='forbid'`; errors `{"error_code"}`.

Out of scope: populating `suitability_rules` (ETL, E6).

## Acceptance criteria
- [ ] Given rules for conservative and aggressive profiles when the tool is called with `conservative` then only conservative rules are returned (test `backend/tests/test_lookup_suitability.py::test_filters_by_profile`).
- [ ] Given `client_risk_profile='reckless'` then the tool returns `{"error_code"}` and issues no SQL (test `test_invalid_enum_rejected`).
- [ ] Given a rule with `min_tier_required` above the principal's tier when the tool runs then it is absent without any tier predicate in the application SQL string (tests `test_rls_filters_rules` and `test_no_tier_predicate_in_sql`).
- [ ] Given 200 matching rules then at most the LIMIT constant are returned and `total_found` reports the returned count (test `test_limit_enforced`).
