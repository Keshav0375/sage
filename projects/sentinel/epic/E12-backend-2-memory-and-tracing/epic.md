---
key: "E12"
title: "Memory and tracing rewrite"
phase: 3
phase_name: "Backend (MVP release)"
repo: "Sentinel"
status: "done"
depends_on: ["E11"]
arch_refs: ["deep-dive/05-data-and-memory.md#5.3", "deep-dive/11-observability-and-ops-dashboard.md#11.1", "ADR-009", "ADR-032"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 54, "id": 5694996395, "url": "https://github.com/Keshav0375/sentinel-brain/issues/54"}
updated: "2026-11-08"
---

## Goal
Episodic and semantic memory on asyncpg + pgvector, embeddings, and Langfuse v3 tracing.

Source: backend phase 2 · branch `dev/backend-phase-2-memory-and-tracing` · PR https://github.com/Keshav0375/Sentinel/pull/20 · signed 2026-10-14.

## Scope
- E12-T1: memory/episodic.py (asyncpg + pgvector)
- E12-T2: memory/semantic.py (asyncpg)
- E12-T3: memory/embeddings.py (pgvector <=>)
- E12-T4: infra/tracing.py → LangFuse (observe + prompts + scoring)

## ADRs
[ADR-009](../../arch/decision-logs.md#adr-009), [ADR-032](../../arch/decision-logs.md#adr-032)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
Memory rewritten Postgres-only with provenance labels (recalled root causes are marked model-generated, unverified); Langfuse v3 observe, prompts and scores with input/output capture off by default. 1646 tests.
