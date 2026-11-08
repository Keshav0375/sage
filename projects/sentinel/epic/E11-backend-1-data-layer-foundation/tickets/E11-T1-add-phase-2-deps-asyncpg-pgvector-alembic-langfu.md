---
key: "E11-T1"
title: "Add MVP deps (asyncpg, pgvector, alembic, langfuse)"
epic: "E11"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: []
arch_refs: ["deep-dive/14-tech-stack.md#14.1", "deep-dive/00-poc-and-the-pivot-to-mvp.md#0.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 50, "id": 5694995724, "url": "https://github.com/Keshav0375/sentinel-brain/issues/50"}
branch: "dev/backend-phase-1-data-layer"
pr: "https://github.com/Keshav0375/Sentinel/pull/19"
updated: "2026-11-08"
---

## Summary
Add MVP dependencies; do NOT remove POC deps yet (§13.5 keeps POC working until

## Description
Source: backend task 1.1 (`sentinel-brain/implementation/tasks/backend/phase-1-data-layer/task-1-phase2-dependencies.md`).

The MVP is proven — removal is Phase 9).

**Files modified:** `pyproject.toml` — add `asyncpg`, `pgvector`, `alembic`, `langfuse`,
ensure `httpx`. Keep `aiosqlite`/`numpy` for now. Update lockfile.

## Acceptance criteria
- [x] New deps resolve and install cleanly; app still imports and boots (POC intact).
- [x] Lockfile regenerated (per CLAUDE.md post-implementation check).

## Outcome
Built: MVP deps added (asyncpg, pgvector, alembic, langfuse v3, sqlalchemy[asyncio]); pip-audit added to dev group; requires-python now >=3.12,<4.0 (langfuse). Commits 3fcfd6e (feat: add MVP deps) + 679343e (fix(deps): clear pip-audit advisories). Files: pyproject.toml, poetry.lock.
User decision 2026-10-10: upgrade pre-existing vulnerable deps inside 1.1 (aiohttp, anyio, cryptography, fsspec, litellm, mcp, multidict, pyasn1, pydantic-settings, pyjwt, python-multipart, sentence-transformers, setuptools, starlette/fastapi 0.143.0, torch, transformers, urllib3). No ignores; openai-agents held at 0.6.4.
Follow-ups: Dockerfile `pip install .` ignores poetry.lock (task 7.1); local Sentinel/.env GROQ_API_KEY empty, so local gate/boot need a dummy key.
Tests: gate VERDICT GREEN, 7 ran, 0 skipped (pip-audit: no known vulnerabilities), run with GROQ_API_KEY=fake-key-for-ci. 1527 tests pass; `sentinel serve` boots.
Verify: `poetry install`; `GROQ_API_KEY=fake-key-for-ci poetry run pytest -q`; `GROQ_API_KEY=fake-key-for-ci poetry run sentinel serve`; `python3 scripts/gate.py backend`.
