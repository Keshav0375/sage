---
key: "E7-T24"
title: "Freeze the pre-registration of the four confirmatory arms"
epic: "E7"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E7-T27", "E7-T23"]
arch_refs: ["decision-logs.md#adr-037", "decision-logs.md#adr-039", "deep-dive/02-quality-attributes.md#2.10"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Write and freeze `docs/eval/preregistration.md` and its machine-readable twin naming exactly the four arms, metrics and rules before any arm runs.

## Description
Done-when (R4 changes of E7): "the pre-registration names exactly the four arms before the first run". Create `data/eval/preregistration.json` and `docs/eval/preregistration.md` with: the four confirmatory arms (ids `ctx_llm_vs_section_prefix`, `voyage_context_4_vs_plain`, `rerank_3_vs_rerank_3_lite`, `structured_lookup_vs_table_chunks`) each with its primary metric (a tier-1 metric of E7-T6), the unit (cluster), the test (sign-flip permutation, exact McNemar for binary metrics), the Holm family of exactly these four, the detectable effect recorded by E7-T27, and the rule that every other arm (datamarking, single-shot query decomposition, cross-lingual query translation, others) is exploratory and cannot enter the default pipeline alone. The temporal validity filter is stated as a correctness control, not an arm. `rerank-2.5` is not listed. The file carries a sha256 of its own canonical JSON in `data/eval/preregistration.sha256`; the ablation runner (E7-T7) refuses to start when the hash does not match or the file changed after the first run's recorded hash.

Out of scope: running the arms (E7-T7).

## Acceptance criteria
- [ ] Given the JSON, then it lists exactly 4 confirmatory arms with the four ids above and a Holm family of size 4 (test `test_prereg.py::test_exactly_four_arms`).
- [ ] Given the JSON, then every arm has a primary metric that exists in the E7-T6 metric list and the detectable-effect value from E7-T27 is present and a number (`test_prereg.py::test_metrics_and_effect_present`).
- [ ] Given an edit to the JSON without updating the sha256 file, then the loader raises `PreregistrationChanged` (`test_prereg.py::test_hash_mismatch_raises`).
- [ ] Given a fifth arm id added to the JSON as confirmatory, then validation fails.
