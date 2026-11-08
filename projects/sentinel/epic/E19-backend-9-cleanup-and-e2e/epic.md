---
key: "E19"
title: "Cleanup and end-to-end"
phase: 3
phase_name: "Backend (Phase 2 release)"
repo: "Sentinel"
status: "done"
depends_on: ["E18"]
arch_refs: ["deep-dive/00-mvp-phase-1-and-the-pivot.md#0.4", "deep-dive/12-evaluation.md#12.2", "ADR-041", "ADR-042"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 91, "id": 5695001980, "url": "https://github.com/Keshav0375/sentinel-brain/issues/91"}
updated: "2026-11-08"
---

## Goal
Delete the Phase-1 artifacts and add an offline end-to-end smoke plus the Langfuse dataset write at the terminal state.

Source: backend phase 9 · branch `dev/backend-phase-9-cleanup` · PR https://github.com/Keshav0375/Sentinel/pull/28 · signed 2026-10-25.

## Scope
- E19-T1: Remove Phase-1 artifacts + deps
- E19-T2: End-to-end integration smoke + eval

## ADRs
[ADR-041](../../arch/decision-logs.md#adr-041), [ADR-042](../../arch/decision-logs.md#adr-042)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
Phase-1 data, generators, SQLite, models, scripts and the SSE route are gone; `/api/scenarios` serves the vendored catalog; offline e2e covers both paths. Then the Phase 2 release: `release-phase-2` merged into `main` as PR #29 (merge commit, `main-backup` kept).
