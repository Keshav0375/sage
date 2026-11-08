---
key: "E21"
title: "Memory hardening, in-cluster eval and README"
phase: 4
phase_name: "Post-release"
repo: "Sentinel"
status: "done"
depends_on: ["E20"]
arch_refs: ["deep-dive/05-data-and-memory.md#5.5", "deep-dive/12-evaluation.md#12.3", "ADR-044", "ADR-045"]
issue: null
updated: "2026-11-08"
---

## Goal
Agent memory that survives teardown and pod restarts, a tool/LLM cache, Azure Managed Redis for hot state, automated eval inside the cluster, and a README for the shipped system.

Source: backend phase 11 · branch `dev/backend-phase-11-memory-hardening` · PR https://github.com/Keshav0375/Sentinel/pull/35 · signed 2026-10-30.

## Scope
- E21-T1: Agent checkpoints, tool/LLM cache, Redis-backed short-term memory
- E21-T2: Azure Managed Redis B0, fail-closed backup and data-only restore
- E21-T3: ci_eval.yml: eval as a Kubernetes Job
- E21-T4: README for the shipped system

## ADRs
[ADR-044](../../arch/decision-logs.md#adr-044), [ADR-045](../../arch/decision-logs.md#adr-045)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
Checkpoints with one bounded resume, Postgres cache with a Redis front, Redis B0 (private endpoint, Entra-only), fail-closed pre-destroy `pg_dump` and data-only restore, `ci_eval.yml` running the eval as a K8s Job under the backend workload identity. Gates GREEN; reviews CONFORMS / SAFE / LGTM after one fix round. Not live-verified: needs the estate up and the infra CI-identity ticket.
