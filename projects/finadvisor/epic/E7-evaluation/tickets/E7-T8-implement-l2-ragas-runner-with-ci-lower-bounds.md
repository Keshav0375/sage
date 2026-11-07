---
key: "E7-T8"
title: "Implement L2 Ragas runner with CI lower bounds"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T1", "E7-T5", "E4-T11"]
arch_refs: ["deep-dive/09-observability.md#9.6", "deep-dive/08-security-and-privacy.md#8.1", "ADR-017", "ADR-005"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Score answers with Ragas collections using the Haiku judge and report metrics with confidence-interval lower bounds.

## Description
Implement the L2 runner: for each answerable case run the real chat pipeline (answer model from `--model`) as fa_eval on the eval tenant, then score with Ragas collections API (pinned version): faithfulness, context precision, context recall, noise sensitivity, plus the deterministic citation score from the E4 CitationVerifier output (do not reimplement the verifier; call E4-T11). Judge model is `LLM_MODEL_JUDGE`; the runner refuses to run if judge == answer model. Report each metric as mean plus a bootstrap 95% confidence interval and its lower bound (ARES-style, arXiv 2311.09476). Refuse to emit gate-eligible numbers unless docs/adr/judge-calibration.md records a go decision (read a machine-readable `judge_calibration.json` written by E7-T1 containing kappa and `go`). Out of scope: the gate comparison (T11).

## Acceptance criteria
- [ ] Unit test: bootstrap CI on a fixed score vector with fixed seed returns the hand-verified lower bound to 3 decimals.
- [ ] Unit test: runner raises when judge model equals answer model.
- [ ] Unit test: runner raises a clear error when judge_calibration.json is missing or has go=false.
- [ ] Integration test with a stub LLM and stub judge on 5 cases produces a result JSON with mean, ci_low, ci_high for faithfulness, context_precision, context_recall, noise_sensitivity and citation.
