---
key: "E7-T19"
title: "Keshav labels the 30-item pilot with the labelling CLI"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T2", "E11-T26"]
arch_refs: ["deep-dive/02-quality-attributes.md#2.10", "deep-dive/10-open-questions.md#10", "decision-logs.md#adr-037"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Build the golden-set labelling CLI and have Keshav label the 30-item pilot (about 6-8 hours) from the first real corpus.

## Description
Human work first. The golden set is labelled by Keshav (K-R4-4: 200 items, about 40-55 h in total, ESTIMATE; ADR-037 says about 39-56 h). The pilot is the first 30 items, about 15% of the set, so about 6-8 h of Keshav's time by the same rate (ESTIMATE). The pilot is separate from the judge calibration of E7-T1 (about 30 labels, rho^2) and the pilot must be finished and its detectable effect recorded (E7-T27) before any other item is labelled or any arm runs (ADR-037, R4-D15).

Engineering part (the ticket's code): `python -m scripts.label_golden` reads the first corpus fixture (E11-T26) from the eval tenant, shows a candidate provision or product, and records for each item the `question`, `slice` (a deep-dive/02 2.10 slice, or `pilot`), `cluster_id` and `cluster_unit` (the provision or product, R4-D17), `expected_evidence` quotes with `doc_key` and `version_key`, an optional `as_of`, and for refusal or injection slices the `expected_refusal` or `must_not_contain`; it writes `labelled_by` and `labelled_at` and appends the time spent to `docs/eval/labelling-log.md`. Public items go to the committed `data/eval/golden_qa.json` (`split: public`); private items (497K, KIDs, ADV brochures) are written only under the private bucket path in `EVAL_PRIVATE_BUCKET_URI` and never into the repo (K-R4-3). Sampling for the pilot: at most 5 items per cluster and spread over at least 6 clusters and at least 3 slices.

Keshav's work in this ticket: label 30 items using the CLI, record hours in the log. Out of scope: the other 170 items (E7-T20, E7-T21), the detectable-effect computation (E7-T27).

## Acceptance criteria
- [ ] Given Keshav's session, when the 30 pilot items are saved, then `data/eval/golden_qa.json` (public) plus the private bucket hold 30 items with `tranche: pilot`, `labelled_by: keshav`, a `cluster_id` and at least one `expected_evidence` quote each (test `test_golden_set.py::test_pilot_complete` reads both locations; the private part skipped with a reason if the bucket is not mounted).
- [ ] Given the pilot file, then no cluster has more than 5 items and there are at least 6 clusters (test `test_golden_set.py::test_pilot_cluster_cap`).
- [ ] Given a private item, when the CLI saves it, then nothing is written under the repo tree; a grep test over the repo fails if any item with `split: private` is found in a committed file.
- [ ] `docs/eval/labelling-log.md` has a row for this session with hours as a number and the item count 30; a CI check fails if the row is missing.
