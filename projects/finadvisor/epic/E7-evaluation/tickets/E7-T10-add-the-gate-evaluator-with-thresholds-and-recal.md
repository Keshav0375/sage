---
key: "E7-T10"
title: "Add the gate evaluator with thresholds and recall baseline"
epic: "E7"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E7-T5"]
arch_refs: ["ADR-017"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Compare run results to the gate thresholds and the stored recall baseline and fail with a clear reason.

## Description
Implement `python -m scripts.eval_gate result.json --baseline data/eval/baseline.json` that exits non-zero if: citation < 0.95, faithfulness < 0.90 (judged on the CI lower bound when the full run, on the point estimate on the PR subset), leaks > 0, or recall@10 drops by more than 2 points versus baseline. Thresholds are constants in config (not scattered). Add `scripts.eval_baseline_update` to write a new baseline (manual, reviewed in PR). Quote ADR-017: "Gate: citation >= 0.95, faithfulness >= 0.90, leaks = 0, recall regression <= 2 pts" and "gate thresholds need re-tuning when the corpus grows". Output a one-line failure reason per breached rule. Out of scope: running the metrics (T6, T8, T9) and CI wiring (T11).

## Acceptance criteria
- [ ] Parametrised unit tests: citation 0.949 fails, 0.95 passes; faithfulness 0.899 fails, 0.90 passes; leaks 1 fails; recall drop 2.1 points fails, 2.0 passes.
- [ ] Each failing case prints the rule name and the measured and required values (asserted by output match).
- [ ] A missing baseline file makes the gate exit non-zero with a message (unit test), never pass silently.
