---
key: "E12-T3"
title: "memory/embeddings.py (pgvector <=>)"
epic: "E12"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E11-T1"]
arch_refs: ["deep-dive/00-mvp-phase-1-and-the-pivot.md#0.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 57, "id": 5694996803, "url": "https://github.com/Keshav0375/sentinel-brain/issues/57"}
branch: "dev/backend-phase-2-memory-and-tracing"
pr: "https://github.com/Keshav0375/Sentinel/pull/20"
updated: "2026-11-08"
---

## Summary
Keep the local embedding model (all-MiniLM-L6-v2, 384-dim); move similarity to the DB

## Description
Source: backend task 2.3 (`sentinel-brain/implementation/tasks/backend/phase-2-memory-and-tracing/task-3-embeddings.md`).

(pgvector `<=>`) instead of numpy cosine. This module now only produces embeddings.

**Files modified:** `src/sentinel/memory/embeddings.py`
- `embed(text) -> list[float]` (384) via sentence-transformers, model name from config.
- Remove numpy cosine helpers (numpy dep formally dropped in Phase 9; if ST needs it transitively, keep as transitive only).
- Cache the model instance; async-safe wrapper if the encode is sync (run in threadpool).

## Acceptance criteria
- [x] `embed()` returns a 384-float vector; deterministic for the same input.
- [x] No cosine-in-Python similarity remains here (moved to pgvector in memory modules).

## Outcome
Built (2b7ae05, `refactor: embeddings produce vectors only; one model load per process`): embeddings now produce vectors only; process-wide model cache keyed by name under a lock; encode via asyncio.to_thread (keeps contextvars/OTel). 384-dim unit vectors. EmbeddingClient API unchanged (alembic 002 and conftest depend on it). No numpy cosine remained here; episodic.py's numpy cosine is task 2.1's job.
Files: src/sentinel/memory/embeddings.py, tests/test_memory/test_embeddings.py. Backend boot proven.
**Tests / gate:** VERDICT GREEN, 7 ran (env -i, only TEST_DATABASE_URL); tree clean, attribution none. 11 tests added.
