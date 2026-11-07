---
key: "E4-T2"
title: "Spike: Presidio latency and recall on synthetic corpus"
epic: "E4"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E1-T21"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#adr-009", "decision-logs.md#adr-036"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 94, "id": 6155680232, "url": "https://github.com/Keshav0375/FinAdvisor/issues/94"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Measure Presidio en_core_web_sm latency and PII recall on English synthetic questions, and measure DE/FR recall without claiming it.

## Description
Spike. No official figure exists (ADR-009). With presidio-analyzer 2.2.x and spaCy en_core_web_sm (PRESIDIO_SPACY_MODEL), run on (a) 500 synthetic advisor questions with injected PII (names, emails, phones, account numbers, national ids, addresses) and (b) 1000-char and 4000-char inputs. Record warm per-call p50/p95, cold-start time, memory, per-entity recall and precision. Test pseudonymization round-trip (placeholders stable within a turn). Propose INPUT_MAX_CHARS and the entity list/score threshold. Record as an ADR-009 addendum.

Round 4 (ADR-036 decision 7, 04 §4.5): Presidio runs ENGLISH ONLY (`en_core_web_sm`); 'DE and FR PII recall is measured before any claim is made'. Add 100 German and 100 French synthetic questions with injected PII, run them through the same English pipeline, and record the recall per entity. The ADR states the DE/FR figures as measurements and states that no DE/FR PII protection is claimed; if recall is below 0.90 the ADR says so. Out of scope: wiring into chat, a DE/FR model.

## Acceptance criteria
- [ ] Given the 500-question English set, when the benchmark runs, then per-entity recall and precision and latency p50/p95 are recorded in the ADR addendum.
- [ ] Given the 100 DE and 100 FR questions, when the benchmark runs, then per-entity recall is recorded and the ADR contains the sentence that DE/FR recall is measured, not claimed, with the numbers.
- [ ] If overall English recall is below 0.90 the ADR lists the missed entity classes and a mitigation; the verdict is stated either way, and the proposed INPUT_MAX_CHARS is justified by the 4000-char latency measurement.
