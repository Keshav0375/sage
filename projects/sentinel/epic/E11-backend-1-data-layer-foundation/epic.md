---
key: "E11"
title: "Data layer foundation"
phase: 3
phase_name: "Backend (MVP release)"
repo: "Sentinel"
status: "done"
depends_on: ["E10"]
arch_refs: ["deep-dive/05-data-and-memory.md#5.1", "ADR-007", "ADR-032"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 49, "id": 5694995545, "url": "https://github.com/Keshav0375/sentinel-brain/issues/49"}
updated: "2026-11-08"
---

## Goal
MVP dependencies, the asyncpg pool, Alembic with the initial schema (3 tables + pgvector) and the seed migration.

Source: backend phase 1 · branch `dev/backend-phase-1-data-layer` · PR https://github.com/Keshav0375/Sentinel/pull/19 · signed 2026-10-12.

## Scope
- E11-T1: Add MVP deps (asyncpg, pgvector, alembic, langfuse)
- E11-T2: asyncpg pool infra/database.py
- E11-T3: Alembic setup + 001_initial_schema
- E11-T4: 002_seed_services migration

## ADRs
[ADR-007](../../arch/decision-logs.md#adr-007), [ADR-032](../../arch/decision-logs.md#adr-032)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
Pool inside the lifespan try/finally; migrations 001 (schema, grants to `gha-app`) and 002 (the one real service row, `sentinel-watchtower`). CI: locked install, 1603 tests passed, 0 skipped.
