---
key: "E11-T4"
title: "002_seed_services migration"
epic: "E11"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E11-T3", "E12-T3"]
arch_refs: ["deep-dive/05-data-and-memory.md#5.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 53, "id": 5694996192, "url": "https://github.com/Keshav0375/sentinel-brain/issues/53"}
branch: "dev/backend-phase-1-data-layer"
pr: "https://github.com/Keshav0375/Sentinel/pull/19"
updated: "2026-11-08"
---

## Summary
> **Amended 2026-10-10 (decision "Backend phase 1"):** seed exactly ONE row, `sentinel-watchtower` (team `sentinel`, tier `standard`, deps `[]`, metadata repo/platform, runbook = the revert-PR rollback procedure + pointer to `Sentinel-deployment/scenarios/README.md`, embedding at seed time). The Phase-1 acme-corp `service_map.json` is NOT seeded; it may only back test fixtures.

## Description
Source: backend task 1.4 (`sentinel-brain/implementation/tasks/backend/phase-1-data-layer/task-4-seed-services-migration.md`).

Seed the `services` table (replaces Phase-1 `data/services/*.json` + `seed.py`). Source the
service registry from the Phase-1 `service_map.json` content, mapped to columns: name, team,
tier, dependencies (JSONB), runbook (markdown), metadata, embedding(384).

**Files created:** `alembic/versions/002_seed_services.py`
- INSERT the known services with their dependencies/runbooks.
- Embedding: compute via the embedding model (all-MiniLM-L6-v2) at migration time, OR insert
  NULL and backfill in a follow-up if the model isn't importable in the migration context —
  **decide and document** (prefer computing so similarity search works immediately).

## Acceptance criteria
- [x] `alembic upgrade head` seeds all services with correct dependencies/runbooks/tier.
- [x] Embeddings populated (or a documented backfill path), so `search services by symptom` returns matches.
- [x] Idempotent-ish (ON CONFLICT (name) DO UPDATE or guarded).

## Outcome
Built `002_seed_services` (Sentinel e26d733, `feat: 002_seed_services — seed sentinel-watchtower with its embedding`). Seeds exactly one row, `sentinel-watchtower`, with a revert-PR runbook and a MiniLM-384 embedding computed at seed time (decision: compute, no backfill). ON CONFLICT upsert, then REINDEX `idx_services_embedding`. Downgrade removes only that row. CI injects a fake embedding client, so the model is never downloaded.
Files: `alembic/versions/002_seed_services.py`, `tests/conftest.py`, `tests/test_infra/test_migrations.py`.
Follow-ups: (1) service lookups must not rely on IVFFlat returning all rows at probes=1 (use a name lookup or `SET ivfflat.probes`) — tools phase. (2) First `alembic upgrade head` on an operator machine downloads the ~90 MB model (`HF_HUB_OFFLINE=1` if cached). (3) Gate needs `GROQ_API_KEY` set in the caller env (local Sentinel/.env has it empty); make gate/test config set a dummy key.
