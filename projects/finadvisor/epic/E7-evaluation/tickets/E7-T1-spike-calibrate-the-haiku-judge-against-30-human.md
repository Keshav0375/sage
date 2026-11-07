---
key: "E7-T1"
title: "Spike: calibrate the Haiku judge against ~30 human labels"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T27"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/09-observability.md#9.6", "decision-logs.md#adr-017", "decision-logs.md#adr-037"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Measure judge-human rho^2 between the Haiku 5.5 judge and about 30 human labels and record whether the judge may gate (rho^2 >= 0.4).

## Description
Spike (must finish before any L2 number is trusted). This is the judge calibration; it is a separate set of about 30 labels and is NOT the 30-item retrieval pilot of E7-T19 (R4 changes of epic E7).

Build a calibration set of about 30 (question, answer, cited excerpts) items drawn from the existing data/eval/golden_qa.json and a few saved model answers, each with a human label for faithfulness and citation correctness stored in data/eval/judge_calibration.json (labels entered by the operator; the ticket supplies the file schema, a labelling CLI `python -m scripts.label_calibration`, and the runner). Run the judge (`LLM_MODEL_JUDGE` = claude-haiku-5-5, must differ from `LLM_MODEL_ANSWER`) with data/eval/judge_prompt.txt as the starting prompt, in both A/B and swapped order where the prompt is pairwise (MT-Bench swap-order check). Human labels are binary pass/fail (R4-D20 Q11); compute rho as the phi coefficient (Spearman on 0/1) between the judge verdict and the human label per metric and report rho^2. Write the machine-readable result `data/eval/judge_calibration.json` {n, rho2 per metric, prompt_hash, judge_model, go} and the human-readable docs/adr/judge-calibration.md (n, rho^2 per metric, confusion table, prompt version, go/no-go statement).

Quote ADR-017 as amended and ADR-037 (amended 2026-11-07): "Judge acceptance is judge-human rho^2 >= 0.4 only." The Haiku judge gates only if rho^2 >= 0.4; the threshold is the config value `JUDGE_MIN_RHO2` = 0.4 (added to 06 6.6 by the arch writer). Trigger to revisit: "Judge-human rho^2 below 0.4" (ADR-037).

Out of scope: the Ragas runner (E7-T8), choosing a different judge model (a no-go result is reported, not fixed here). Cohen's kappa is no longer the acceptance measure.

## Acceptance criteria
- [ ] Given the ~30 labelled items, `python -m scripts.calibrate_judge` prints rho^2 for faithfulness and citation and exits 0; a unit test with a fixed fake judge and known labels asserts rho^2 equals the hand-computed value to 3 decimals (test `test_calibrate_judge.py::test_rho2_matches_hand_value`).
- [ ] data/eval/judge_calibration.json has n >= 30, a rho2 value per metric, the judge model id, the prompt file hash and `go` equal to (every rho2 >= 0.4); a unit test with rho2 0.39 asserts `go == false` and with 0.40 asserts `go == true`.
- [ ] Unit test: the calibration runner raises if LLM_MODEL_JUDGE equals LLM_MODEL_ANSWER.
- [ ] docs/adr/judge-calibration.md exists and contains n, rho^2 per metric, judge model id, prompt hash and the go or no-go decision next to the threshold 0.4; a CI grep test fails if any is missing.
