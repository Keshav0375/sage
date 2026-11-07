---
key: "E7-T8"
title: "Implement L2 Ragas runner with CI lower bounds"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T1", "E7-T5", "E7-T23", "E4-T11"]
arch_refs: ["deep-dive/09-observability.md#9.6", "deep-dive/08-security-and-privacy.md#8.1", "decision-logs.md#adr-017", "decision-logs.md#adr-037", "decision-logs.md#adr-005"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 188, "id": 6263564108, "url": "https://github.com/Keshav0375/FinAdvisor/issues/188"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Score answers with Ragas collections using the Haiku judge, gated on judge-human rho^2 >= 0.4, and report metrics with confidence-interval lower bounds.

## Description
Implement the L2 runner: for each answerable case run the real chat pipeline (answer model from `--model`) as fa_eval on the eval tenant, then score with the Ragas collections API (pinned version): faithfulness, context precision, context recall, noise sensitivity, plus the deterministic citation score from the E4 CitationVerifier output (do not reimplement the verifier; call E4-T11). Judge model is `LLM_MODEL_JUDGE`; the runner refuses to run if judge == answer model.

Report each metric as the mean plus a 95% confidence interval and its lower bound. For the real set the interval is computed over clusters (resample or aggregate per `cluster_id`, not per item; see E7-T23); the bootstrap over items is used only for the `synthetic` split (ARES-style, arXiv 2311.09476). Gating (ADR-037, amended 2026-11-07): the runner refuses to emit gate-eligible judge numbers unless `data/eval/judge_calibration.json` (E7-T1) has `go: true`, i.e. rho^2 >= 0.4 for every metric used; without it the runner still emits the tier-1 deterministic metrics of E7-T6 and marks the judge metrics `exploratory`.

Out of scope: the gate comparison (E7-T10).

## Acceptance criteria
- [ ] Unit test: the cluster-level interval on a fixed score vector with fixed seed and 2 clusters returns the hand-verified lower bound to 3 decimals (`test_l2.py::test_cluster_ci_lower_bound`).
- [ ] Unit test: runner raises when judge model equals answer model.
- [ ] Unit test: runner marks the judge metrics `exploratory` and emits no `gate_eligible` field when judge_calibration.json is missing or has go=false (rho2 0.39), and emits them gate-eligible with rho2 0.41.
- [ ] Integration test with a stub LLM and stub judge on 5 cases produces a result JSON with mean, ci_low, ci_high for faithfulness, context_precision, context_recall, noise_sensitivity and citation.
