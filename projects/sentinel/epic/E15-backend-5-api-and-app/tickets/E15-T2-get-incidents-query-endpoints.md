---
key: "E15-T2"
title: "GET /incidents* query endpoints"
epic: "E15"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E12-T1", "E13-T5"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 74, "id": 5694999480, "url": "https://github.com/Keshav0375/sentinel-brain/issues/74"}
branch: "dev/backend-phase-5-api"
pr: "https://github.com/Keshav0375/Sentinel/pull/23"
updated: "2026-11-08"
---

## Summary
Read endpoints over incident history.

## Description
Source: backend task 5.2 (`sentinel-brain/implementation/tasks/backend/phase-5-api/task-2-incident-query-endpoints.md`).

**Files created/modified:** `src/sentinel/api/incidents.py`
- `GET /incidents?status=&service=&limit=` — filtered list.
- `GET /incidents/{id}` — single.
- `GET /incidents/{id}/trajectory` — full agent trace (JSONB).
- `GET /incidents/{id}/deploy` — linked `deployments` record.
- Token-protected; typed Pydantic responses.

## Acceptance criteria
- [x] All four routes return the documented shapes; filters work; 401 without token; 404 for unknown id.

## Outcome
Built 2026-10-18, commit 71cb06e (cherry-picked from 5667f33): incident query endpoints over episodic memory: list, single, trajectory, linked deploy; shapes = §5.3 columns; in-flight from STM; 404/503; auth mounted by 5.5.
Tests: 31 added. Integrated gate (backend, env -i + TEST_DATABASE_URL): VERDICT GREEN (7 ran). Live boot: /health ok, /ready 200.
Review fixes 2026-10-21 (d0f7ae9..d27a8f3, status stays done-pending-review): e37fea5 GET /incidents limit capped at 200. Gate on d27a8f3: VERDICT GREEN (full run, 7 ran, 0 skipped, TEST_DATABASE_URL set); boot OK (/health 200, /ready 200, protected 401, clean exit).
