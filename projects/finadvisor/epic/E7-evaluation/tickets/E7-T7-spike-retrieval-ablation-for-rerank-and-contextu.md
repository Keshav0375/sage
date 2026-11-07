---
key: "E7-T7"
title: "Spike: run the four confirmatory ablation arms with Holm"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T6", "E7-T21", "E7-T23", "E7-T24", "E7-T27", "E3-T16", "E5-T14", "E6-T8", "E11-T17", "E11-T21", "E6-T22", "E4-T34"]
arch_refs: ["decision-logs.md#adr-037", "decision-logs.md#adr-016", "decision-logs.md#adr-008", "decision-logs.md#adr-017", "decision-logs.md#adr-039", "deep-dive/02-quality-attributes.md#2.10", "deep-dive/06-interfaces-and-contracts.md#6.6"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Run exactly the four pre-registered confirmatory arms on the labelled 200-item set through the Message Batches API and record keep or drop decisions.

## Description
Spike. Supersedes the earlier rerank and contextual-retrieval-only ablation (R4 changes of E7; ADR-037 as amended 2026-11-07, ADR-039 V1). Using the L1 runner (E7-T6), the cluster-level statistics (E7-T23) and the frozen pre-registration (E7-T24), run on the full labelled set (only after E7-T21 and with the private bucket mounted where private items exist):

1. LLM contextual retrieval (`claude-haiku-5-5` headers, ADR-016) vs the free section-path prefix (`contextual: llm` vs `section_path_prefix`).
2. `voyage-context-4` contextualized chunks vs plain chunks.
3. `rerank-3` vs `rerank-3-lite` (the default; the full model enters only with a measured gain, ADR-039 V1). `rerank-2.5` is not an arm.
4. Structured lookup (SEC RR facts, KID fee tables) vs table chunks.

Each arm is a paired comparison per cluster; p-values come from per-cluster aggregation then sign-flip permutation (exact McNemar for binary metrics), with the Holm correction over exactly these four. The primary metric of each arm is the one named in the pre-registration. Record recall@5/10/15, MRR, nDCG@10 and first-stage and rerank p95 latency per arm (checked against first stage p95 <= 600 ms and rerank p95 < 700 ms, 9.5). Slices under 30 items are exact tests or `exploratory`.

Exploratory arms (datamarking, single-shot query decomposition, cross-lingual query translation, any other) may be run, are written to a separate section marked `exploratory`, and the runner refuses to write a config default from an exploratory arm alone (D-R4-3).

Budget and batching: all LLM calls of an ablation run (header generation, answers, judge) go through the Anthropic Message Batches API (50% off) and the runner asserts it; the run is capped by `EVAL_BUDGET_USD` (E7-T5).

Write docs/adr/retrieval-ablation.md with the per-arm table and, per arm, the decision (kept or dropped, with the effect in points, the Holm-adjusted p and the latency delta), and apply the decided defaults to `Settings` (`RERANK_MODEL`, `CONTEXTUAL_RETRIEVAL_ENABLED`, embed variant, table handling) as a config change only. Quote ADR-037: "At most 4 confirmatory ablation arms with Holm; other arms are exploratory and cannot enter the default pipeline alone." Out of scope: GATE_MIN_SCORE (E3-T16), building the arm variants: arm 2 data is the eval-only `voyage-context-4` generation of E6-T22, arm 4 is the flagged `lookup_fund_facts` tool of E4-T34 (with the SEC RR facts of E11-T17 and the KIDs of E11-T21).

## Acceptance criteria
- [ ] Given the runner config, when listing confirmatory arms, then there are exactly 4 and their ids equal the pre-registration file of E7-T24 (test `test_ablation.py::test_exactly_four_confirmatory_arms`).
- [ ] Given a stub LLM, when the ablation runner calls the model, then every call goes through the Batches client and a direct `messages.create` call fails the test (`test_ablation.py::test_calls_use_batches_api`).
- [ ] Given EVAL_BUDGET_USD below the estimated cost, when the runner starts, then it aborts before the first batch is submitted (`test_ablation.py::test_budget_abort`).
- [ ] Given an exploratory arm that beats the default by 10 points, when the report is generated, then it is marked `exploratory` and the default-writing step raises (`test_ablation.py::test_exploratory_cannot_set_default`).
- [ ] docs/adr/retrieval-ablation.md has one row per confirmatory arm with effect, adjusted p and latency as numbers (a grep test fails on empty cells), and the `Settings` defaults equal its decisions (unit test reads both).
