---
key: "E7-T25"
title: "PII guardrail eval: openpii-1.5m and Gretel finance sets"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T5", "E4-T8", "E9-T5"]
arch_refs: ["deep-dive/02-quality-attributes.md#2.10", "deep-dive/09-observability.md#9.9", "deep-dive/11-tech-stack.md#11", "decision-logs.md#adr-037", "decision-logs.md#adr-036"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 181, "id": 6263553292, "url": "https://github.com/Keshav0375/FinAdvisor/issues/181"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Measure per-class PII precision and recall, including German and French recall, on sampled openpii-1.5m and Gretel finance sets and export the gauges.

## Description
Implements the PII guardrail set of deep-dive/02 2.10: "2,000 sampled en/de/fr from ai4privacy openpii-1.5m (CC-BY-4.0 per card) + 2,000 Gretel finance multilingual (Apache-2.0); per-class precision and recall; IBAN and account numbers get generated cases with valid checksums." And 04 and 11: Presidio runs with `en_core_web_sm` (English only), "DE and FR PII recall is measured before any claim is made" (ADR-036). Build `jobs eval --guardrails pii`:
- A fetch script `scripts/fetch_guardrail_sets.py pii` downloads the two datasets to a git-ignored local folder (never committed), samples with a fixed seed, and records each dataset's licence string, card URL and fetch date in `data/eval/guardrail_sets.json` (licence recorded at integration; the run fails if a recorded licence is missing).
- A generator for IBAN and account-number cases with valid checksums (mod-97 for IBAN) so the must-redact classes are covered.
- A runner that passes each text through the production input guard path (Presidio pseudonymization, E4-T8) and scores per class and per language (en, de, fr) precision and recall; the report lists DE and FR recall explicitly.
- Gauges `guard_precision{guard}` and `guard_recall{guard}` via `metrics.record` (E9-T5; the registry label is `guard` only, so the gauge is the aggregate over the must-redact classes and the per-class and per-language numbers stay in the report), plus per-guard p95 latency checked against the 150 ms rule of 9.9. Pass lines (PII recall >= 0.90 on must-redact classes) are the author's proposals, reported as `proposed`, not gates.
Out of scope: the injection sets (E7-T26), changing the guard.

## Acceptance criteria
- [ ] Given a fixed seed, when the sampler runs on a 10,000-row stub of each dataset, then it returns 2,000 + 2,000 rows with the same ids on a second run (test `test_guardrail_pii.py::test_sampling_deterministic`).
- [ ] Given generated IBANs, then every one passes mod-97 and a corrupted one fails the generator's own validator (`test_guardrail_pii.py::test_iban_checksum`).
- [ ] Given a stub guard that redacts only English, when the runner scores a DE and an FR fixture, then the report shows recall for `de` and `fr` as numbers lower than `en` and the run does not claim a pass for DE or FR (`test_guardrail_pii.py::test_de_fr_recall_reported`).
- [ ] Given `data/eval/guardrail_sets.json` with a missing licence field, then the run exits non-zero before scoring.
- [ ] Given a completed run, then `guard_precision` and `guard_recall` are recorded once per guard through the registry with only the `guard` label (a test captures the calls; an unknown label raises as in E9-T5).
