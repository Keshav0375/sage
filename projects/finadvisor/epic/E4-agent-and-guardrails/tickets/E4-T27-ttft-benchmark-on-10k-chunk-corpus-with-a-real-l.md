---
key: "E4-T27"
title: "TTFT benchmark to first complete sentence, 10k-chunk corpus"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T19", "E3-T16"]
arch_refs: ["deep-dive/02-quality-attributes.md#2.1", "deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#adr-036", "decision-logs.md#adr-039"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Measure TTFT to the first complete sentence against the 2.1 target and fail if above.

## Description
Script and CI-manual job: load the 10k-chunk synthetic corpus (E3-T16 fixture), real Voyage and Anthropic (claude-sonnet-5-5), Presidio on, prompt cache warm; run at least 200 turns including 30% follow-ups and a cache-hit mix reported separately, once with MODEL_ARMOR_ENABLED true and once false. Round 4 (ADR-036: 'First visible text is the first complete sentence, not the first token'): TTFT = request received to the first `delta` event, which by construction holds the first complete sentence after redaction and the release checks. Targets from 2.1, unchanged: p50 < 2.0 s and p95 < 3.5 s; the first-stage retrieval leg is reported against p95 <= 600 ms (ADR-039 M3). The script exits non-zero above the TTFT targets. Report per-stage p50/p95 (guard, embed/screen, retrieval, rerank, LLM first token, sentence buffer and release checks). Save results in the repo docs and an ADR note.

## Acceptance criteria
- [ ] Given the 10k corpus and real LLM, when the benchmark runs 200 turns, then TTFT to first complete sentence is p50 < 2.0 s and p95 < 3.5 s or the command exits non-zero.
- [ ] The report lists per-stage p50/p95 including the sentence-buffer and release-check stage, and the first-stage retrieval p95 against 600 ms.
- [ ] Cache-hit and cache-miss turns, and Model Armor on and off, are reported as separate distributions.
