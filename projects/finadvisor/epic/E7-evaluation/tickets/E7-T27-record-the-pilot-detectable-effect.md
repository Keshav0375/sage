---
key: "E7-T27"
title: "Compute and record the detectable effect from the pilot"
epic: "E7"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E7-T19", "E7-T6", "E7-T23"]
arch_refs: ["decision-logs.md#adr-037", "deep-dive/02-quality-attributes.md#2.10", "deep-dive/10-open-questions.md#10"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Run the baseline on the 30 pilot items, compute the effect size the 200-item set can detect, and record it before any other item is labelled or any arm runs.

## Description
ADR-037: "the detectable effect is computed after a 30-item pilot and recorded" and "Pilot-based detectable-effect record exists before arms run"; no ICC or n_eff is assumed. Run the L1 tier-1 metrics (E7-T6) on the default pipeline for the pilot items, aggregate per cluster (E7-T23), and estimate the between-cluster spread of each arm's primary metric difference. Using that spread, compute by simulation (sign-flip permutation, the same test as the arms) the smallest difference that a 40-cluster set would detect at the Holm-adjusted level for 4 arms (alpha 0.05 / 4 as the most conservative step) with 80% power. Write `docs/eval/detectable-effect.md` and `data/eval/detectable_effect.json` {date, pilot_n, pilot_clusters, spread, alpha, power, simulation_draws, seed, detectable_effect_pp}. If the value is above 10 pp the file says so (ADR-037 trigger to revisit: "the pilot shows a detectable effect above 10 pp") and the ticket does not change the plan itself.

Out of scope: choosing arms or thresholds, labelling (E7-T20, E7-T21).

## Acceptance criteria
- [ ] Given a stub pilot result with a known per-cluster spread, when the computation runs with a fixed seed, then `detectable_effect_pp` equals the hand-verified simulation value within 0.5 pp (`test_detectable_effect.py::test_known_spread`).
- [ ] `data/eval/detectable_effect.json` exists with every listed field non-null and a CI check fails if it is missing or older than the pilot file's last change.
- [ ] Given a value above 10 pp, then the markdown file contains the line `above 10 pp: revisit` (`test_detectable_effect.py::test_flags_above_10pp`).
- [ ] The labelling CLI of E7-T19 refuses to label item 31 while the JSON is absent (`test_label_cli.py::test_blocks_until_effect_recorded`).
