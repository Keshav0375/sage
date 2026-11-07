---
key: "E7-T3"
title: "Add adversarial, refusal and leak-probe cases to the golden set"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T2"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.1", "deep-dive/02-quality-attributes.md#2.10", "decision-logs.md#adr-017", "decision-logs.md#adr-037"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 184, "id": 6263556060, "url": "https://github.com/Keshav0375/FinAdvisor/issues/184"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add the cross-tenant, tier and jurisdiction probe set and fixtures, and the structure for the two refusal and injection slices of the 200-item set.

## Description
Two parts.

(1) Probe set (synthetic, not part of the 200 and not part of any cluster statistic): at least 25 `split: synthetic` cases, at least 5 in each of cross_tenant, tier, jurisdiction, refusal (NO_FIRM_DOCUMENTATION, out-of-jurisdiction, above-tier) and adversarial (prompt injection in the question and in retrieved text). A cross-tenant probe is a question whose only matching content belongs to another tenant, so the right answer is a refusal and no foreign chunk id may appear (`forbidden_chunk_ids`). Add seed fixtures (a second synthetic tenant with distinct content, plus restricted-tier and other-jurisdiction documents inside the `eval` tenant) under data/eval/fixtures/ so the probes have something to leak. Quote ADR-017 L3: "cross-tenant / tier / jurisdiction refusal and promptfoo red team" and the OWASP LLM01/LLM08 tests of 8.1.

(2) Slice templates for the real set: the two 2.10 slices "unanswerable, out-of-scope and ACL refusal" (20 items) and "injection-in-document" (10 items) get their case templates, labelling guidance and a validator that checks each real item in those slices sets `expected_refusal` or `must_not_contain`. The real items are authored from the first corpus and labelled by Keshav in E7-T20 and E7-T21; this ticket does not author them.

Out of scope: the runner that executes them (E7-T9), the guardrail sets (E7-T25, E7-T26).

## Acceptance criteria
- [ ] `pytest backend/tests/test_golden_set.py::test_probe_counts` asserts >= 5 probe cases in each of cross_tenant, tier, jurisdiction, refusal and adversarial, all `split: synthetic`.
- [ ] Test asserts every cross_tenant case names a foreign-tenant chunk id in `forbidden_chunk_ids` that exists in the fixtures.
- [ ] Loading the fixtures into a test database via the seed path creates documents for two tenants; the test fails if the second tenant has no chunks.
- [ ] Given a real item in slice `unanswerable_refusal` or `injection_in_document` with neither `expected_refusal` nor `must_not_contain`, the slice validator fails (test `test_golden_set.py::test_refusal_slices_need_expectation`).
