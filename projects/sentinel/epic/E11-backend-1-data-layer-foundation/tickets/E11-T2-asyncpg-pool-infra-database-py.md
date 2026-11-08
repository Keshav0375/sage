---
key: "E11-T2"
title: "asyncpg pool infra/database.py"
epic: "E11"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E11-T1"]
arch_refs: ["deep-dive/04-agent-pipeline.md#4.6", "deep-dive/05-data-and-memory.md#5.1", "deep-dive/00-mvp-phase-1-and-the-pivot.md#0.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 51, "id": 5694995858, "url": "https://github.com/Keshav0375/sentinel-brain/issues/51"}
branch: "dev/backend-phase-1-data-layer"
pr: "https://github.com/Keshav0375/Sentinel/pull/19"
updated: "2026-11-08"
---

## Summary
New `src/sentinel/infra/database.py` — asyncpg pool (parallel to old `db.py`, which stays

## Description
Source: backend task 1.2 (`sentinel-brain/implementation/tasks/backend/phase-1-data-layer/task-2-asyncpg-database-pool.md`).

until Phase 9 per §13.5 step 2).

**Files created:** `src/sentinel/infra/database.py`
- `async def create_pool(dsn: str, *, min_size=2, max_size=10) -> asyncpg.Pool` (bounds from config).
- Register the `pgvector` codec on each connection (`pgvector.asyncpg.register_vector`).
- `@asynccontextmanager acquire()` helper; module-level pool holder set at lifespan startup, closed at shutdown.
- `from __future__ import annotations`, full type hints, structured logging.

## Acceptance criteria
- [x] Pool creates/acquires/releases; vector codec registered; min/max honored from config.
- [x] Clean async lifecycle (no leaked connections); errors wrapped in `MemoryError` per exception hierarchy.

## Outcome
Built asyncpg + pgvector pool in `infra/database.py`: `create_pool(dsn, *, min_size, max_size, password=str|callable)`, `register_vector` via init, `acquire()` helper; lifespan opens pool only when DATABASE_URL is a Postgres URL. `SentinelError` hierarchy in `sentinel/exceptions.py`; added dev dep asyncpg-stubs.
Commits (Sentinel): 12bb1c2 feat: asyncpg + pgvector pool in infra/database.py; bdaa4dc fix: blank DATABASE_URL in .env.example; never-blank pool errors.
Files: src/sentinel/infra/database.py, exceptions.py, config.py, main.py, CONVENTIONS.md, tests/conftest.py, tests/test_infra/test_database.py, tests/test_config.py, pyproject.toml, poetry.lock, .env.example.
Notes: local Sentinel/.env has stale Azure placeholder DSN picked up by litellm load_dotenv; blank it or point at container. conftest session fixture creates vector extension until 1.3 alembic replaces it.
