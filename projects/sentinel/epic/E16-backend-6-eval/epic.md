---
key: "E16"
title: "Eval"
phase: 3
phase_name: "Backend (MVP release)"
repo: "Sentinel"
status: "done"
depends_on: ["E15"]
arch_refs: ["deep-dive/12-evaluation.md#12.1", "ADR-037", "ADR-035"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 79, "id": 5695000222, "url": "https://github.com/Keshav0375/sentinel-brain/issues/79"}
updated: "2026-11-08"
---

## Goal
The judge writing Langfuse scores and the eval runner scoring scenario runs against `branches.yaml`.

Source: backend phase 6 · branch `dev/backend-phase-6-eval` · PR https://github.com/Keshav0375/Sentinel/pull/24 · signed 2026-10-24.

## Scope
- E16-T1: eval/judge.py → LangFuse scores
- E16-T2: eval/runner.py → LangFuse datasets

## ADRs
[ADR-037](../../arch/decision-logs.md#adr-037), [ADR-035](../../arch/decision-logs.md#adr-035)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
Read-only judge (0-1 per dimension, anchored on ground truth); `run_eval.py` scores runs from dataset `sentinel-scenario-runs`, writes the eval report and `incidents.eval_score`. Live eval needs real scenario runs and LLM keys.
