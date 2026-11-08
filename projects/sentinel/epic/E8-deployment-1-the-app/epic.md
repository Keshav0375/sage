---
key: "E8"
title: "The app"
phase: 2
phase_name: "Deployment"
repo: "Sentinel-deployment"
status: "done"
depends_on: ["E6"]
arch_refs: ["deep-dive/08-deployment-and-scenarios.md#8.1", "ADR-030"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 39, "id": 5694993955, "url": "https://github.com/Keshav0375/sentinel-brain/issues/39"}
updated: "2026-11-08"
---

## Goal
A deliberately minimal FastAPI app, `sentinel-watchtower`, with three routes and a fixed startup log line: the thing Sentinel watches.

Source: deployment phase 1 · branch `dev/deploy-phase-1-app` · PR https://github.com/Keshav0375/Sentinel-deployment/pull/1 · signed 2026-10-04.

## Scope
- E8-T1: FastAPI app (3 routes + startup log + config)
- E8-T2: App tests (health / version / root)

## ADRs
[ADR-030](../../arch/decision-logs.md#adr-030)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
App with config, startup log, `/`, `/health`, `/version`, exact-pinned dependencies and 4 tests; merged by squash.
