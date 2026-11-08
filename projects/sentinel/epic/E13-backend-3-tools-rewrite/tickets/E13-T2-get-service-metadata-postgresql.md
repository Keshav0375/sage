---
key: "E13-T2"
title: "get_service_metadata → PostgreSQL"
epic: "E13"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E12-T2", "E13-T1"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 61, "id": 5694997529, "url": "https://github.com/Keshav0375/sentinel-brain/issues/61"}
branch: "dev/backend-phase-3-tools"
pr: "https://github.com/Keshav0375/Sentinel/pull/21"
updated: "2026-11-08"
---

## Summary
Rewrite `get_service_metadata` to read the `services` table (was JSON seed). `@function_tool`,

## Description
Source: backend task 3.2 (`sentinel-brain/implementation/tasks/backend/phase-3-tools/task-2-service-lookup.md`).

typed I/O, read-only, no external state, structured error return (never raise raw).

**Files modified:** `src/sentinel/tools/service_lookup.py`
- Input `ServiceLookupInput{service_name}` → Output `ServiceMetadata{team, tier, dependencies, runbook, ...}` or structured `ToolError`.
- Uses injected semantic memory (DI, not singleton).

## Acceptance criteria
- [x] Returns metadata from Postgres; unknown service → structured not-found (no raise).
- [x] Pydantic v2 I/O; read-only; docstring = tool description.

## Outcome
Built `get_service_metadata` on Postgres: returns typed `SemanticRecord` or `ToolFailure{tool,kind,message}` (not_found/unavailable/bad_input). Commit 63fc81f. Files: models/tools.py (new: ToolFailure, ServiceLookupInput), tools/service_lookup.py, tests (test_service_lookup, test_models/test_tools, test_semantic).
