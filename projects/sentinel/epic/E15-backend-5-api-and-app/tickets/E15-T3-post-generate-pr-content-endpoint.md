---
key: "E15-T3"
title: "POST /generate/pr-content endpoint"
epic: "E15"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E14-T4"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.3"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 75, "id": 5694999631, "url": "https://github.com/Keshav0375/sentinel-brain/issues/75"}
branch: "dev/backend-phase-5-api"
pr: "https://github.com/Keshav0375/Sentinel/pull/23"
updated: "2026-11-08"
---

## Summary
The single endpoint that serves rollback PR content (demo PRs do NOT use it).

## Description
Source: backend task 5.3 (`sentinel-brain/implementation/tasks/backend/phase-5-api/task-3-generate-pr-content-endpoint.md`).

**Files created:** `src/sentinel/api/generate.py`
- `POST /generate/pr-content` — input per §3.4 (incident_id, root_cause, evidence_summary, confidence, target_deploy, resolution_type), token-protected → calls the `pr_content_generator` agent → `{title, description, model_used, tokens_used}`.

## Acceptance criteria
- [x] Endpoint returns the §3.4 response shape; title `revert:`-prefixed; 401 without token.
- [x] Only wired to the agent (no PR creation here — GHA does that).

## Outcome
Built 2026-10-18, commit a9477f2 (from ee94c2d): POST /generate/pr-content; service from the stored incident; 404 unknown, 409 no matching deploy, 503 DB/unavailable, 502 after fallback; text only, never a PR.
Tests: 16 added. Integrated gate (backend, env -i + TEST_DATABASE_URL): VERDICT GREEN (7 ran). Live boot: /health ok, /ready 200.
Review fixes 2026-10-21 (d0f7ae9..d27a8f3, status stays done-pending-review): 17edf2b agents SDK errors (AgentsException) map to 502. Gate on d27a8f3: VERDICT GREEN (full run, 7 ran, 0 skipped, TEST_DATABASE_URL set); boot OK (/health 200, /ready 200, protected 401, clean exit).
