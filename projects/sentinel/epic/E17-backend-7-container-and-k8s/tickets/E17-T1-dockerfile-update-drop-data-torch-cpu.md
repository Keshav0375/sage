---
key: "E17-T1"
title: "Dockerfile update (drop data/, torch-cpu)"
epic: "E17"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: []
arch_refs: ["deep-dive/07-backend-hosting-and-ci.md#7.1", "deep-dive/00-mvp-phase-1-and-the-pivot.md#0.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 83, "id": 5695000782, "url": "https://github.com/Keshav0375/sentinel-brain/issues/83"}
branch: "dev/backend-phase-7-container-and-k8s"
pr: "https://github.com/Keshav0375/Sentinel/pull/26"
updated: "2026-11-08"
---

## Summary
Update the image: copy `src/` + `alembic/` (no `data/`), install with torch-cpu index to

## Description
Source: backend task 7.1 (`sentinel-brain/implementation/tasks/backend/phase-7-container-and-k8s/task-1-dockerfile-update.md`).

keep the image small.

**Files modified:** `Dockerfile`
- `python:3.12-slim`; apt `libpq-dev gcc`; `pip install -r requirements.txt` with `PIP_EXTRA_INDEX_URL=https://download.pytorch.org/whl/cpu`; `COPY src/ alembic/ alembic.ini`; **no `COPY data/`**; `CMD uvicorn sentinel.main:app --host 0.0.0.0 --port 8000`.

## Acceptance criteria
- [x] `docker build` succeeds; image runs and serves `/health`; no `data/` in the image; torch is cpu build (~80 MB not ~2 GB).

## Outcome
Built 2026-10-24. Commits 3f4980c "refactor: lock-based arm64 image; LLM keys read from Key Vault" + 0730682 "refactor: bake the embedding model into the image; run offline" on dev/backend-phase-7-container-and-k8s (rebased onto release-phase-2 d0e58f4).
- Multi-stage arm64 image (2.47 GB), installs from poetry.lock (scripts/install_locked.py --main-only), torch 2.14.1+cpu, no CUDA/nvidia/triton. Non-root uid 10001, PYTHONPATH=/app/src; has alembic/, alembic.ini, src/; no data/.
- all-MiniLM-L6-v2 baked into /opt/hf, HF_HUB_OFFLINE=1, TRANSFORMERS_OFFLINE=1. uvicorn --timeout-graceful-shutdown 5 (5+37=42 s < 45 s grace).
- KV loader reads anthropic-api-key and openai-api-key into Settings (no env mirroring).
- Tooling: PR #25 (d0e58f4) bumped setuptools/filelock + dated filelock CVE ignore (expires 2026-11-24). Decisions: dd95eef.
Review fixes 1729dbf (2026-10-24): base image pinned to python:3.12-slim@sha256:6c6ae362...e90f (arm64); model pinned to revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 (embeddings.py PINNED_REVISIONS). `docker run --read-only --tmpfs /tmp --tmpfs /app/reports --network none` returns /health 200. Gate VERDICT GREEN on 1729dbf (full run, 7 ran, 0 skipped); boot OK. Decisions: dd95eef, b384323.
