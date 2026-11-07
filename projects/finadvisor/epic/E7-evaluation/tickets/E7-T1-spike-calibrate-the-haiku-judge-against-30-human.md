---
key: "E7-T1"
title: "Spike: calibrate the Haiku judge against ~30 human labels"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T27"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/09-observability.md#9.6", "ADR-017"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Measure Cohen's kappa between the Haiku 5.5 judge and ~30 human labels and record whether L2 numbers can be trusted.

## Description
Spike (must finish before any L2 number is trusted). Build a calibration set of ~30 (question, answer, cited excerpts) items drawn from the existing data/eval/golden_qa.json and a few saved model answers, each with a human label for faithfulness (pass/fail) and citation correctness (pass/fail) stored in data/eval/judge_calibration.json (labels entered by the operator; the ticket supplies the file schema, a labelling CLI `python -m scripts.label_calibration`, and the runner). Run the judge (`LLM_MODEL_JUDGE` = claude-haiku-5-5, must differ from `LLM_MODEL_ANSWER`) with the existing data/eval/judge_prompt.txt as the starting prompt, in both A/B and swapped order where the prompt is pairwise (MT-Bench swap-order check). Compute Cohen's kappa per metric. Write the result to docs/adr/judge-calibration.md with: n, kappa per metric, confusion matrix, prompt version, and a go/no-go statement. Quote ADR-017: "Haiku 5.5 judge ... calibrated on ~30 human labels (Cohen's kappa)"; trigger to revisit: "Judge kappa below acceptable". Out of scope: the Ragas runner (E7-T8), choosing a different judge model (a no-go result is reported, not fixed here).

## Acceptance criteria
- [ ] Given the ~30 labelled items, `python -m scripts.calibrate_judge` prints kappa for faithfulness and citation and exits 0; a unit test with a fixed fake judge and known labels asserts the kappa value equals the hand-computed value (e.g. 0.6) to 3 decimals.
- [ ] docs/adr/judge-calibration.md exists in the repo and contains n >= 30, a kappa value per metric, the judge model id and the prompt file hash; a CI check (grep test) fails if any of these is missing.
- [ ] Unit test: the calibration runner raises if LLM_MODEL_JUDGE equals LLM_MODEL_ANSWER.
- [ ] The ADR states an explicit threshold used for go/no-go and the decision (go or no-go) next to the measured kappa.
