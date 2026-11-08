---
key: "E4-T2"
title: "CI runner image (Dockerfile + build-push)"
epic: "E4"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E2-T1"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.5"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 19, "id": 5694990855, "url": "https://github.com/Keshav0375/sentinel-brain/issues/19"}
branch: "dev/infra-phase-4-wiring-and-ci"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/4"
updated: "2026-11-08"
---

## Summary
Custom CI runner image (Python 3.12 + ruff/pyright/pytest + asyncpg/pgvector/alembic + az

## Description
Source: infra task 4.2 (`sentinel-brain/implementation/tasks/infra/phase-4-wiring-and-ci/task-2-ci-runner-image.md`).

CLI) so sentinel workflows don't reinstall tools each run.

**Files created:**
- `ci-images/ci-runner.Dockerfile` — per §6.1 (python:3.12-slim; apt curl gcc libpq-dev git docker.io; pip ruff pyright pytest pytest-asyncio asyncpg pgvector alembic; Azure CLI).
- `ci-images/build-push.sh` — `az acr login`, docker build, docker push `sentinelacr0375.azurecr.io/ci-runner:latest` (the one-time manual bootstrap, §6.2).

## Acceptance criteria
- [x] Image builds locally; contains ruff, pyright, pytest, az, kubectl-adjacent tools.
- [x] `build-push.sh` tags/pushes `ci-runner:latest` to ACR.

## Outcome
_not yet implemented_
