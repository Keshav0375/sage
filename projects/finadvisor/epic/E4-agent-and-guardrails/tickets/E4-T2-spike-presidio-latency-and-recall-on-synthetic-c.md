---
key: "E4-T2"
title: "Spike: Presidio latency and recall on synthetic corpus"
epic: "E4"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E1-T21"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#ADR-009"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 94, "id": 6155680232, "url": "https://github.com/Keshav0375/FinAdvisor/issues/94"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Measure Presidio en_core_web_sm latency and PII recall on the synthetic corpus.

## Description
Spike. No official figure exists (ADR-009). With presidio-analyzer 2.2.x and spaCy en_core_web_sm (PRESIDIO_SPACY_MODEL), run on (a) 500 synthetic advisor questions with injected PII (names, emails, phones, account numbers, national ids, addresses) and (b) 1000-char and 4000-char inputs. Record warm per-call p50/p95, cold-start time, memory, and per-entity recall and precision. Test pseudonymization round-trip (placeholders stable within a turn). Record as an ADR-009 addendum; propose INPUT_MAX_CHARS and the entity list/score threshold. Out of scope: wiring into chat.

## Acceptance criteria
- [ ] Given the 500-question set, when the benchmark runs, then per-entity recall and precision and latency p50/p95 are recorded in the ADR addendum.
- [ ] If overall recall on injected PII is below 0.90 the ADR lists the missed entity classes and a mitigation (custom recognizer or lower threshold); the verdict is stated either way.
- [ ] The proposed INPUT_MAX_CHARS is justified by the 4000-char latency measurement.
