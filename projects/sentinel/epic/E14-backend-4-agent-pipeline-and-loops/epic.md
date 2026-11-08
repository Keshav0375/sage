---
key: "E14"
title: "Agent pipeline and loops"
phase: 3
phase_name: "Backend (MVP release)"
repo: "Sentinel"
status: "done"
depends_on: ["E13"]
arch_refs: ["deep-dive/04-agent-pipeline.md#4.2", "deep-dive/04-agent-pipeline.md#4.5", "ADR-034", "ADR-035", "ADR-006"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 67, "id": 5694998431, "url": "https://github.com/Keshav0375/sentinel-brain/issues/67"}
updated: "2026-11-08"
---

## Goal
Provider routing with fallback, the orchestrator with plan-execute, reflexion, reverification and budget, the loop prompts and the PR content generator.

Source: backend phase 4 · branch `dev/backend-phase-4-agents` · PR https://github.com/Keshav0375/Sentinel/pull/22 · signed 2026-10-19.

## Scope
- E14-T1: Provider routing + fallback (providers/)
- E14-T2: Orchestrator: plan-execute + reflexion + reverification + budget
- E14-T3: reflexion.txt + reverification.txt prompts
- E14-T4: pr_content_generator agent + prompt

## ADRs
[ADR-034](../../arch/decision-logs.md#adr-034), [ADR-035](../../arch/decision-logs.md#adr-035), [ADR-006](../../arch/decision-logs.md#adr-006)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
Python orchestrator with code-enforced caps, a distinct judge with a `judge_conflict` guard, the R14 Langfuse generation bridge and the vendor trace exporter removed. Verified on the fake LLM only (1925 tests); no real-LLM run yet.
