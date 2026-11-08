---
key: "E17"
title: "Container and K8s"
phase: 3
phase_name: "Backend (MVP release)"
repo: "Sentinel"
status: "done"
depends_on: ["E16"]
arch_refs: ["deep-dive/07-backend-hosting-and-ci.md#7.1", "deep-dive/07-backend-hosting-and-ci.md#7.2", "ADR-038"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 82, "id": 5695000663, "url": "https://github.com/Keshav0375/sentinel-brain/issues/82"}
updated: "2026-11-08"
---

## Goal
Lock-based arm64 image, K8s manifests with workload identity, and the composite actions.

Source: backend phase 7 · branch `dev/backend-phase-7-container-and-k8s` · PR https://github.com/Keshav0375/Sentinel/pull/26 · signed 2026-10-24.

## Scope
- E17-T1: Dockerfile update (drop data/, torch-cpu)
- E17-T2: azure/k8s/ deployment + service manifests
- E17-T3: Composite actions (backend-up/down, kv-secrets, teams, psql)

## ADRs
[ADR-038](../../arch/decision-logs.md#adr-038)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
Non-root image with the embedding model baked in and pinned; Deployment, Service, ConfigMap, NetworkPolicy with read-only root and no auto-mounted SA token; seven SHA-pinned composite actions. Nothing verified live.
