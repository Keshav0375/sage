---
key: "E7-T2"
title: "Define the golden-set schema and loader with tenant parameters"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T27"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/06-interfaces-and-contracts.md#6.6", "ADR-017"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Give the golden set a validated, tenant-parameterised schema and migrate the existing 50-or-fewer cases into it.

## Description
The repo already has data/eval/golden_qa.json and scripts/run_eval.py (MVP). Define a Pydantic model `GoldenCase` {id, category (answerable, adversarial, refusal, cross_tenant, tier, jurisdiction), question, persona (advisor tier, jurisdictions, licenses, role as a template, never a hard-coded tenant id), tenant_param (placeholder resolved to the `eval` tenant via `EVAL_TENANT_ID` at run time), expected_chunk_ids or expected_doc_refs (for L1), must_cite_refs, must_not_contain, expected_refusal (code or null), reference_answer (optional, for Ragas), notes}. Add a loader `load_golden(path)` that validates every case, rejects duplicate ids and unknown categories, and resolves tenant parameters. Convert the existing cases to the schema (target: 50 cases at this ticket). Quote ADR-017: "Golden set 50 growing to ~300, tenant-parameterised." Out of scope: adding cases beyond 50 (E7-T3), runners.

## Acceptance criteria
- [ ] Given a golden file with a duplicate id, `load_golden` raises ValueError naming the id (unit test).
- [ ] Given a case with a hard-coded tenant uuid instead of the placeholder, validation fails (unit test).
- [ ] `pytest backend/tests/test_golden_set.py` passes and asserts the shipped file holds >= 50 cases covering every category name at least once except where E7-T3 adds them.
- [ ] With EVAL_TENANT_ID set to uuid X, every resolved case reports tenant_id == X (unit test).
