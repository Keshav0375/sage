---
key: "E20"
title: "Ops dashboard"
phase: 4
phase_name: "Post-release"
repo: "Sentinel"
status: "done"
depends_on: ["E19", "E7"]
arch_refs: ["deep-dive/11-observability-and-ops-dashboard.md#11.3", "ADR-043"]
issue: null
updated: "2026-11-08"
---

## Goal
A public, observe-only dashboard of builds, deploys, incidents, agent runs, revert PRs and reviews, eval and traces, backed by an append-only git ledger and served from GitHub Pages.

Source: backend phase 10 · branch `dev/backend-phase-10-ops-dashboard` · PR https://github.com/Keshav0375/Sentinel/pull/33 · signed 2026-10-28.

## Scope
- E20-T1: Append-only ops ledger, ops-event action and frozen ops.v1 schema
- E20-T2: Every backend and infra workflow emits ops events
- E20-T3: Reconciler and snapshot builder
- E20-T4: React SPA in dashboard-web/
- E20-T5: Pages deploy, web CI and pre-publish guard

## ADRs
[ADR-043](../../arch/decision-logs.md#adr-043)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
Ledger, event action, reconciler, React SPA and Pages workflows shipped. e2e 18/18; Lighthouse median perf 0.97, a11y 1.00. Reviews: architecture CONFORMS, safety SAFE, code LGTM after 2 rounds. GitHub Pages is not enabled yet (owner step), so https://keshav0375.github.io/Sentinel/ is not live.
