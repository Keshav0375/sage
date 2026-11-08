---
key: "E15-T4"
title: "/health + /ready probes"
epic: "E15"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E11-T2"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1", "deep-dive/07-backend-hosting-and-ci.md#7.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 76, "id": 5694999781, "url": "https://github.com/Keshav0375/sentinel-brain/issues/76"}
branch: "dev/backend-phase-5-api"
pr: "https://github.com/Keshav0375/Sentinel/pull/23"
updated: "2026-11-08"
---

## Summary
Liveness + readiness. Open (no token) so K8s + backend-up can probe.

## Description
Source: backend task 5.4 (`sentinel-brain/implementation/tasks/backend/phase-5-api/task-4-health-ready-probes.md`).

**Files created/modified:** `src/sentinel/api/health.py`
- `GET /health` → 200 `{"status":"ok"}` (liveness, always if process up).
- `GET /ready` → 200 `{"status":"ready"}` when DB connected + models loaded; else 503 `{"status":"not_ready"}`. Under `SENTINEL_FAKE_LLM=1`, skip the live-provider check (§9.1).

## Acceptance criteria
- [x] `/health` 200 always; `/ready` reflects DB connectivity (503 when pool down); no token required.
- [x] FAKE_LLM mode makes `/ready` deterministic for CI.

## Outcome
Built 2026-10-18, commit 7827e0c: /health returns {"status":"ok"}; /ready pings the DB pool (no DB configured -> ready; configured but down -> 503).
Tests: 17 added. Integrated gate (backend, env -i + TEST_DATABASE_URL): VERDICT GREEN (7 ran). Live boot: /health ok, /ready 200.
Review fixes 2026-10-21 (d0f7ae9..d27a8f3, status stays done-pending-review): 070a30b /ready reads database_configured from the wired Settings. Gate on d27a8f3: VERDICT GREEN (full run, 7 ran, 0 skipped, TEST_DATABASE_URL set); boot OK (/health 200, /ready 200, protected 401, clean exit).
