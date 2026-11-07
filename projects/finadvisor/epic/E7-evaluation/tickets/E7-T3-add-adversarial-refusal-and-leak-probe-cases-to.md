---
key: "E7-T3"
title: "Add adversarial, refusal and leak-probe cases to the golden set"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T2"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.1", "ADR-017"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Extend the golden set with adversarial, refusal, and cross-tenant / tier / jurisdiction probe cases.

## Description
Add at least 40 cases to the golden set: prompt-injection attempts in the question and in retrieved text, requests the system must refuse (no firm documentation -> NO_FIRM_DOCUMENTATION refusal, out-of-jurisdiction, above-tier content), and cross-tenant probes (a question whose only matching content belongs to another tenant, so the right answer is a refusal and no foreign chunk id may appear). Each case sets expected_refusal or must_not_contain. Add seed fixtures (a second synthetic tenant with distinct content, plus restricted-tier and other-jurisdiction documents inside the `eval` tenant) under data/eval/fixtures/ so that probes have something to leak. Quote ADR-017 L3: "cross-tenant / tier / jurisdiction refusal and promptfoo red team" and OWASP table LLM01/LLM08 tests. Out of scope: the runner that executes them (E7-T10).

## Acceptance criteria
- [ ] `pytest backend/tests/test_golden_set.py` asserts >= 40 cases in categories adversarial, refusal, cross_tenant, tier, jurisdiction, with at least 5 in each.
- [ ] Test asserts every cross_tenant case names a foreign-tenant chunk id in a `forbidden_chunk_ids` field that exists in the fixtures.
- [ ] Loading the fixtures into a test database via the existing seed path creates documents for two tenants and the test fails if the second tenant has no chunks.
