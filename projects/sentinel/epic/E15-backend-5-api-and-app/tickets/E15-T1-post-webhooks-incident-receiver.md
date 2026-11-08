---
key: "E15-T1"
title: "POST /webhooks/incident receiver"
epic: "E15"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E14-T2", "E12-T1", "E15-T5", "E15-T6"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/04-agent-pipeline.md#4.6"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 73, "id": 5694999346, "url": "https://github.com/Keshav0375/sentinel-brain/issues/73"}
branch: "dev/backend-phase-5-api"
pr: "https://github.com/Keshav0375/Sentinel/pull/23"
updated: "2026-11-08"
---

## Summary
The webhook that triggers the pipeline. Accepts the GHA-enriched payload, launches an

## Description
Source: backend task 5.1 (`sentinel-brain/implementation/tasks/backend/phase-5-api/task-1-webhook-receiver.md`).

isolated asyncio task per incident, returns 202 immediately.

**Files created/modified:** `src/sentinel/api/webhooks.py`
- `IncidentPayload` Pydantic model per §3.1 (source, alert_id, dd_event_id, correlation_id, **signal_type**, title, severity, tags{service, deploy_status, failed_stage, version}, context{service_metadata, pr_details, recent_logs}, timestamp, raw_payload).
- `POST /webhooks/incident` (dep: `require_incident_write`) → generate `incident_id`, spawn `handle_incident` task with its own ShortTermMemory + LangFuse trace (§4.5), passing `signal_type` for the two-case branch, return 202 `{incident_id, correlation_id, status:"accepted"}`.
- Store terminal incident to episodic memory on completion.

## Acceptance criteria
- [x] 202 with incident_id; pipeline runs as an independent task (concurrent incidents isolated).
- [x] **401 without a valid Entra bearer** (missing, wrong audience, expired, or no `Incident.Write`
- [x] `signal_type` is required and drives the two-case branch (`deploy_failure` → rollback fast
- [x] Terminal incident persisted with trajectory + resolution_type.

## Outcome
Built `POST /webhooks/incident` (backend commit ac630a0, plus 360496a `fix(deps): certifi 2026.10.19` for unrelated advisory PYSEC-2026-4320). 25 files, ~41 tests.
- Replaces the POC `/webhooks/alert`, AlertDeduplicator and AlertAck.
- `IncidentPayload` requires signal_type/correlation_id/title; tags as object or comma string; severity/alert_id/service default "unknown".
- Duplicate correlation_id -> 202 with the original incident_id, status `duplicate`.
- One task per incident with its own STM; fast path pinned to `context.pr_details.sha` (7-char prefix rule); on rollback_proposed `deployments.incident_id` is backfilled.
Review fixes 2026-10-21 (d0f7ae9..d27a8f3, status stays done-pending-review): d9ead3f IncidentTasks (concurrency cap 429, drain, 503, task error logging); 31a79b0 body cap 413 + bounded alert context; 05a1bda per-incident pipeline timeout; d27a8f3 503 on shutdown during the dedupe lookup, nothing recorded. Gate on d27a8f3: VERDICT GREEN (full run, 7 ran, 0 skipped, TEST_DATABASE_URL set); boot OK (/health 200, /ready 200, protected 401, clean exit).
