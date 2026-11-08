---
key: "E18"
title: "CI/CD workflows"
phase: 3
phase_name: "Backend (Phase 2 release)"
repo: "Sentinel"
status: "done"
depends_on: ["E17"]
arch_refs: ["deep-dive/07-backend-hosting-and-ci.md#7.4", "ADR-039", "ADR-015"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 86, "id": 5695001243, "url": "https://github.com/Keshav0375/sentinel-brain/issues/86"}
updated: "2026-11-08"
---

## Goal
PR gate, post-merge deploy, the incident-response pipeline and the scale toggle.

Source: backend phase 8 · branch `dev/backend-phase-8-cicd` · PR https://github.com/Keshav0375/Sentinel/pull/27 · signed 2026-10-25.

## Scope
- E18-T1: ci_validation.yml (fast PR gate)
- E18-T2: ci_backend_deployment.yml (post-merge deploy)
- E18-T3: ci_incident_response.yml (real pipeline)
- E18-T4: ci_backend_scale.yml (scale toggle + nightly)

## ADRs
[ADR-039](../../arch/decision-logs.md#adr-039), [ADR-015](../../arch/decision-logs.md#adr-015)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
Four workflows plus a `resolve-stable-tag` action, every action pinned by SHA, the `guard-main-source.yml` script injection fixed, the rollback-spec endpoint added. Nothing run live; the PR's own CI was the first real run of `ci_validation.yml`.
