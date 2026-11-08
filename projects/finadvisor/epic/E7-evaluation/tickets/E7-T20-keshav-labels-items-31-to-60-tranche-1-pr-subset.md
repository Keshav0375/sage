---
key: "E7-T20"
title: "Keshav labels items 31 to 60 to complete tranche 1"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T27", "E7-T3"]
arch_refs: ["deep-dive/02-quality-attributes.md#2.10", "decision-logs.md#adr-037"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 176, "id": 6263548947, "url": "https://github.com/Keshav0375/FinAdvisor/issues/176"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Keshav labels 30 more items (about 6-8 hours) so tranche 1, the 60-item PR subset, is complete.

## Description
Only after the pilot's detectable effect is recorded (E7-T27). Keshav labels items 31 to 60 with `python -m scripts.label_golden` (E7-T19), so that pilot plus these 30 items form tranche 1 = 60 items, which is the PR subset of the eval gate (deep-dive/02 2.10: "Tranche 1 = 60 items (the PR subset), tranche 2 = 140"). Estimated Keshav time: about 6-8 h (ESTIMATE, same rate as the 40-55 h for 200 items). Slices to cover in tranche 1 follow the 2.10 list (single-hop US, EU and UK; tables and fee numbers; temporal as-of; refusal; injection-in-document; and so on), and each cluster still has at most 5 items. Items in the two refusal and injection slices use the templates of E7-T3. Public items go to the committed file, private items only to the private bucket (K-R4-3).

Out of scope: tranche 2 (E7-T21), PR workflow wiring (E7-T11).

## Acceptance criteria
- [ ] Given the labelled files, then exactly 60 items have `tranche` in (`pilot`, 1) with `labelled_by: keshav` (public plus private; the private count is read from the bucket when mounted) (test `test_golden_set.py::test_tranche1_is_60`).
- [ ] Given tranche 1, then no cluster has more than 5 items and every slice present in tranche 1 appears in the 2.10 slice list (test `test_golden_set.py::test_tranche1_slices_and_cap`).
- [ ] Given the PR subset selection of E7-T5, when `--subset pr` runs on the shipped file with the private bucket mounted, then it selects exactly these 60 items.
- [ ] `docs/eval/labelling-log.md` has a row for this session with hours as a number and the item count 30.
