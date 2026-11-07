---
key: "E7-T7"
title: "Spike: retrieval ablation for rerank and contextual retrieval"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T6", "E3-T16", "E5-T14"]
arch_refs: ["ADR-008", "ADR-016", "ADR-017", "deep-dive/06-interfaces-and-contracts.md#6.6"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Run dense / FTS / hybrid / rerank (with and without contextual headers) ablation and record the decisions.

## Description
Spike. Using E7-T6, run these configs over the full golden set: dense, FTS, hybrid (RRF k=60), hybrid + rerank with RERANK_CANDIDATES in {10, 15, 20, 30}, each with CONTEXTUAL_RETRIEVAL_ENABLED on and off (requires the corpus re-indexed with and without `chunks.context_header`). Record recall@5/10/15, MRR, nDCG@10 and first-stage / rerank p95 latency. Write docs/adr/retrieval-ablation.md with the table and these decisions: RERANK_ENABLED (kept or dropped), RERANK_CANDIDATES (value in range 10-30), CONTEXTUAL_RETRIEVAL_ENABLED (kept or dropped). Quote ADR-008: "kept or dropped by the eval ablation on recall and latency; `RERANK_CANDIDATES` default 15 (range 10-30), set by the L1 ablation (D14.1)" and ADR-016: "The L1 ablation decides whether it stays." The ticket also records the latency budget check: first stage p95 < 300 ms, rerank p95 < 700 ms. Out of scope: GATE_MIN_SCORE (set in E3-T16). Applying the chosen values to config defaults is part of this ticket (config change only).

## Acceptance criteria
- [ ] docs/adr/retrieval-ablation.md exists with one row per config containing recall@10, MRR, nDCG@10 and p95 latency as numbers; a grep test fails on empty cells.
- [ ] The ADR states RERANK_ENABLED, RERANK_CANDIDATES (between 10 and 30) and CONTEXTUAL_RETRIEVAL_ENABLED each as kept/dropped or a value, with the recall delta in points and latency delta in ms that justify it.
- [ ] The default values in `Settings` equal the ADR decisions (unit test reads both).
- [ ] Rerun of the winning config reproduces recall@10 within 1 point of the ADR value (command recorded in the ADR).
