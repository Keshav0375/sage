---
key: "E4-T8"
title: "Guard-in: input cap and Presidio pseudonymization"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T2", "E4-T4"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#ADR-009"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 100, "id": 6155687152, "url": "https://github.com/Keshav0375/FinAdvisor/issues/100"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Cap input length and pseudonymize PII before embed, LLM, traces and logs.

## Description
In src/guardrails: reject over INPUT_MAX_CHARS with INPUT_TOO_LONG (413) before any other work; Presidio AnalyzerEngine (spaCy PRESIDIO_SPACY_MODEL=en_core_web_sm, loaded once per process at startup, entity list/threshold from spike E4-T2) returns the redacted text plus a placeholder map held only in request memory. The redacted text is the only text passed to embedding, Model Armor, LLM, Langfuse, OTel attributes and logs. Replace the MVP src/pii fallback. Quote ADR-009: 'Presidio in-process pseudonymization ... before embed / LLM / traces / logs'. Out of scope: output redaction.

## Acceptance criteria
- [ ] Given a question containing an email, a phone number and a person name, when guard-in runs, then the returned text has none of them and contains typed placeholders (unit test).
- [ ] Given input of INPUT_MAX_CHARS+1, when guard-in runs, then INPUT_TOO_LONG is raised before the Presidio engine is invoked (mock call count 0).
- [ ] Given the benchmark corpus from E4-T2, recall is at least the value recorded in the ADR (regression test with threshold).
- [ ] Warm p95 latency on a 1000-char input stays within the ADR-recorded bound (marked perf test).
