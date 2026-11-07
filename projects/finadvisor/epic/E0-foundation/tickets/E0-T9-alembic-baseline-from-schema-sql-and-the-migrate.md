---
key: "E0-T9"
title: "Alembic baseline from schema.sql and the migrate entrypoint"
epic: "E0"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T2", "E0-T3"]
arch_refs: ["deep-dive/01-context-and-goals.md#1", "deep-dive/04-components-and-responsibilities.md#4", "decision-logs.md#adr-019", "decision-logs.md#adr-021", "deep-dive/11-tech-stack.md#migrations"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 10, "id": 6155579937, "url": "https://github.com/Keshav0375/FinAdvisor/issues/10"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
`python -m src.entrypoint jobs migrate` upgrades an empty database to a schema identical to `backend/db/schema.sql`, and the image gets its `api` and `jobs` entrypoints.

## Description
Why: G-12: `schema.sql` is never applied by the app and there is no migration tool. plan.md E0: "Alembic baseline created from `schema.sql`; `migrate` entrypoint"; done when "Alembic upgrade on an empty database equals the baseline schema". ADR-019: one image with entrypoints `api | worker | jobs`; §4.8: the `migrate` job runs Alembic upgrade before traffic (in the cloud as `fa_owner`; roles arrive in E1, so locally it runs as the configured `DB_USER`).

Build:
- Add Alembic 1.20 (deep-dive/11-tech-stack.md) as a main dependency and re-lock.
- `backend/alembic.ini` (no URL inside), `backend/migrations/env.py` (async engine on asyncpg, URL from `Settings().database_dsn`), `backend/migrations/versions/0001_baseline.py` whose `upgrade()` creates exactly the objects in `backend/db/schema.sql` (extensions `vector` and `pgcrypto`, the four tables, indexes, RLS and policy, the guarded role creation) embedded as SQL in the migration so it stays immutable; `downgrade()` drops them. asyncpg runs one statement per execute: split statements or use a sync-style `exec_driver_sql` per statement. Keep `backend/db/schema.sql` untouched as the golden reference for the equality test.
- `backend/src/entrypoint.py`: `python -m src.entrypoint api` starts uvicorn (`0.0.0.0`, port from `PORT`, default 8000, one process); `python -m src.entrypoint jobs migrate` runs `alembic upgrade head`; any other command exits 2 with usage. Set the Dockerfile `ENTRYPOINT ["python","-m","src.entrypoint"]` and `CMD ["api"]` for the runtime stage (the dev stage keeps its reload command).
- Copy `alembic.ini` and `migrations/` into the image.

Out of scope: the target data model, partitioning, roles and RLS v2 (E1 adds further revisions), the `worker` entrypoint (E5; see questions), tenant onboarding flag.

## Acceptance criteria
- [ ] Given an empty Postgres (`pgvector/pgvector:0.8.5-pg16`), when `python -m src.entrypoint jobs migrate` runs, then it exits 0 and `SELECT version_num FROM alembic_version` returns `0001`; a second run exits 0 and changes nothing (integration test).
- [ ] Given database A built with `psql -f backend/db/schema.sql` and database B built by the migrate entrypoint, `pg_dump --schema-only --no-owner --no-privileges` of both, normalised for the `alembic_version` table, is byte-identical (integration test; fails on any drift).
- [ ] Given database B at head, `alembic downgrade base` leaves zero tables in `public` other than `alembic_version` (integration test).
- [ ] Given `DB_PORT` pointing at a closed port, `jobs migrate` exits non-zero within 30 s and the output contains no DB password (subprocess test).
- [ ] `docker run --rm fa-backend:test bogus` exits 2, and `docker run --rm fa-backend:test jobs migrate` against the compose Postgres exits 0 (checked in the PR).
- [ ] `poetry check --lock`, ruff and mypy pass with the new files.
