---
key: "E7-T2"
title: "Define the golden-set schema and loader with clusters and splits"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T27"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/06-interfaces-and-contracts.md#6.6", "deep-dive/02-quality-attributes.md#2.10", "decision-logs.md#adr-017", "decision-logs.md#adr-037"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 175, "id": 6263548064, "url": "https://github.com/Keshav0375/FinAdvisor/issues/175"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Give the golden set a validated, tenant-parameterised schema with cluster, slice, tranche and public/private fields, and migrate the existing MVP cases as the synthetic split.

## Description
The repo already has data/eval/golden_qa.json and scripts/run_eval.py (MVP). Define a Pydantic model `GoldenCase`:
- `id`, `category` (answerable, adversarial, refusal, cross_tenant, tier, jurisdiction), `question`, `persona` (advisor tier, jurisdictions, licenses, role as a template, never a hard-coded tenant id), `tenant_param` (placeholder resolved to the `eval` tenant via `EVAL_TENANT_ID` at run time), `must_cite_refs`, `must_not_contain`, `expected_refusal` (code or null), `reference_answer` (optional), `notes`.
- R4 fields (ADR-037, deep-dive/02 2.10): `split` in (`synthetic`, `public`, `private`); `cluster_id` and `cluster_unit` in (`cfr_section`, `eu_article`, `eu_annex`, `cobs_section`, `uk_provision`, `fund`, `kid`, `brochure`) (the cluster is the provision or product, not the file; required for `public` and `private`); `slice` (one of the 2.10 slice names, or `pilot`); `tranche` in (`pilot`, 1, 2) where tranche 1 is the 60-item PR subset; `as_of` (optional date); `expected_evidence` (list of {doc_key, version_key, quote}) used by the evidence-span recall, gold-version-in-top-5 and numeric-in-span checks of E7-T6; `labelled_by` and `labelled_at` (set by the labelling CLI of E7-T19).
- `expected_chunk_ids` stays optional and only for `synthetic` cases (chunk ids are not stable across parser versions).

Add a loader `load_golden(path, private_bucket=None)` that validates every case, rejects duplicate ids and unknown categories, resolves tenant parameters, and skips `private` cases when the private bucket is not mounted (config `EVAL_PRIVATE_BUCKET_URI` unset; the name is added to 06 6.6), returning the skipped count so reports can print it (K-R4-3: private items run only where the private bucket is mounted; no private text is ever committed). Convert the existing MVP cases to the schema as `split: synthetic` (they drive the harness and the PR gate until the real set exists, and are excluded from every cluster statistic). Quote ADR-037: "200 items, public/private split ... the cluster unit is the PROVISION or PRODUCT, not the whole file."

Out of scope: the real items (E7-T19 to E7-T21), the cluster-rule check (E7-T22), runners.

## Acceptance criteria
- [ ] Given a golden file with a duplicate id, `load_golden` raises ValueError naming the id (test `test_golden_set.py::test_duplicate_id`).
- [ ] Given a case with a hard-coded tenant uuid instead of the placeholder, validation fails (test `test_golden_set.py::test_hardcoded_tenant`).
- [ ] Given a `public` or `private` case without `cluster_id` or with an unknown `cluster_unit`, validation fails; a `synthetic` case without them passes (test `test_golden_set.py::test_cluster_required_for_real_items`).
- [ ] Given a file with 3 private cases and no private bucket, `load_golden` returns the other cases and `skipped_private == 3`; with the bucket set it returns all (test `test_golden_set.py::test_private_skipped_without_bucket`).
- [ ] With EVAL_TENANT_ID set to uuid X, every resolved case reports tenant_id == X; `pytest backend/tests/test_golden_set.py` passes on the shipped migrated file, which holds >= 50 `synthetic` cases.
