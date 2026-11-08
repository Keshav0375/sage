---
key: "E15"
title: "API and app"
phase: 3
phase_name: "Backend (Phase 2 release)"
repo: "Sentinel"
status: "done"
depends_on: ["E14"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1", "deep-dive/09-1-identity-plane.md#9.12", "ADR-036", "ADR-016"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 72, "id": 5694999205, "url": "https://github.com/Keshav0375/sentinel-brain/issues/72"}
updated: "2026-11-08"
---

## Goal
The webhook receiver with the `signal_type` branch, incident queries, the PR-content endpoint, probes, the lifespan with workload-identity wiring, and Entra bearer auth.

Source: backend phase 5 · branch `dev/backend-phase-5-api` · PR https://github.com/Keshav0375/Sentinel/pull/23 · signed 2026-10-23.

## Scope
- E15-T1: POST /webhooks/incident receiver
- E15-T2: GET /incidents* query endpoints
- E15-T3: POST /generate/pr-content endpoint
- E15-T4: /health + /ready probes
- E15-T5: main.py lifespan + concurrency + token auth
- E15-T6: api/auth.py — Entra bearer validation (JWKS)

## ADRs
[ADR-036](../../arch/decision-logs.md#adr-036), [ADR-016](../../arch/decision-logs.md#adr-016)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
Webhook with dedupe, body and concurrency caps and a pipeline timeout; Entra v2 JWKS auth with an audience list; Entra-token DB pool; bounded shutdown. Carried: worst-case shutdown 37 s vs the 30 s K8s grace (fixed in phase 7 with 45 s).
