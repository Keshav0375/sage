---
key: "E4-T27"
title: "TTFT benchmark on 10k-chunk corpus with a real LLM"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T19", "E3-T16"]
arch_refs: ["deep-dive/02-quality-attributes.md#2.1", "deep-dive/04-components-and-responsibilities.md#4.5"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Measure TTFT p50/p95 against the deep-dive/02-quality-attributes.md §2.1 target and fail if above.

## Description
Script and CI-manual job: load the 10k-chunk synthetic corpus (E3-T16 fixture), real Voyage and Anthropic (claude-sonnet-5-5), Model Armor and Presidio on, prompt cache warm; run at least 200 turns including 30% follow-ups and a cache-hit mix reported separately. TTFT = request received to first delta event. Report p50/p95, stage breakdown (guard, embed/screen, retrieval, rerank, LLM first token). Targets from deep-dive/02-quality-attributes.md §2.1: p50 < 2.0 s, p95 < 3.5 s; script exits non-zero above them. Save results in the repo docs and an ADR note.

## Acceptance criteria
- [ ] Given the 10k corpus and real LLM, when the benchmark runs 200 turns, then p50 < 2.0 s and p95 < 3.5 s or the command exits non-zero.
- [ ] The report lists per-stage p50/p95 so a regression is attributable.
- [ ] Cache-hit and cache-miss turns are reported as separate distributions.
