---
key: "E7-T21"
title: "Keshav labels tranche 2 (140 items) and the intra-rater check"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T20", "E7-T22"]
arch_refs: ["deep-dive/02-quality-attributes.md#2.10", "deep-dive/10-open-questions.md#10", "decision-logs.md#adr-037"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 177, "id": 6263549830, "url": "https://github.com/Keshav0375/FinAdvisor/issues/177"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Keshav labels the last 140 items (about 28-39 hours) to reach the 200-item set, then relabels 15% a week later to check his own agreement.

## Description
Keshav labels tranche 2 (140 items) with `python -m scripts.label_golden`, finishing the 200-item set of deep-dive/02 2.10: slices summing to 200 (single-hop US 25 / EU 25 / UK 15; tables and fee numbers 25; temporal as-of, superseded, revoked 30; multi-document and cross-jurisdiction 20; cross-lingual 20; unanswerable, out-of-scope and ACL refusal 20; injection-in-document 10; compliance checks 10), about 165 public and about 35 private items. Labelling the 200 items is 40-55 h (ESTIMATE; ADR-037 says about 39-56 h) and the intra-rater relabel adds about 6-8 h, about 46-63 h in all; this ticket's labelling part is about 28-39 h of Keshav's time over several sessions, each logged in `docs/eval/labelling-log.md`. The sampling rule must hold: at least 40 clusters (provision or product), at most 5 items per cluster, so 200 items are exactly 5 items in each of 40 clusters unless the corpus yields more usable provisions and the floor is raised (ADR-037 amended).

Intra-rater check (2.10: "15% relabelled after one week; agreement >= 0.8 or the labelling guide is revised; no second reviewer exists"): after at least 7 days, the CLI draws 30 items (15% of 200) at random, hides the old labels, Keshav relabels them (about 6-8 h extra by the same rate; with it Keshav's total is about 46-63 h, R4-D20 Q13; ESTIMATE), and `python -m scripts.intra_rater` writes the agreement on the evidence spans and the as-of or refusal fields to `docs/eval/intra-rater.md`. If agreement is below 0.8, the labelling guide `docs/eval/labelling-guide.md` is revised and the affected slice relabelled.

Out of scope: the cluster-rule check itself (E7-T22), the ablations (E7-T7).

## Acceptance criteria
- [ ] Given all labelled files (public in the repo, private in the bucket), then there are 200 items with `labelled_by: keshav` and the slice counts equal the 2.10 list (test `test_golden_set.py::test_full_set_slice_counts`; the private part is read when mounted, otherwise the test asserts public items >= 165 and the count of missing private items equals 200 minus the loaded count).
- [ ] `python -m scripts.golden_stats --check` (E7-T22) exits 0 on the full set.
- [ ] `docs/eval/intra-rater.md` exists with n = 30, the date of the first and the second labelling at least 7 days apart, and an agreement number; a CI check fails if the dates are closer than 7 days or the number is below 0.8 without a revised-guide commit referenced in the file.
- [ ] `docs/eval/labelling-log.md` rows sum to a number of items equal to 140 for tranche 2, and hours are recorded per session.
