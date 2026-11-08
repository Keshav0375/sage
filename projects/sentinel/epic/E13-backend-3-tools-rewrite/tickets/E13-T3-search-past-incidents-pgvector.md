---
key: "E13-T3"
title: "search_past_incidents → pgvector"
epic: "E13"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E12-T1", "E12-T3", "E13-T1"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 62, "id": 5694997679, "url": "https://github.com/Keshav0375/sentinel-brain/issues/62"}
branch: "dev/backend-phase-3-tools"
pr: "https://github.com/Keshav0375/Sentinel/pull/21"
updated: "2026-11-08"
---

## Summary
Rewrite `search_past_incidents` to embed the symptom and query episodic memory via pgvector.

## Description
Source: backend task 3.3 (`sentinel-brain/implementation/tasks/backend/phase-3-tools/task-3-incident-search.md`).

**Files modified:** `src/sentinel/tools/incident_search.py`
- Input `IncidentSearchInput{symptom_text, k}` → Output list of `SimilarIncident{id, root_cause, resolution_type, similarity}`.
- Read-only; uses injected episodic memory + embeddings.

## Acceptance criteria
- [x] Returns top-k similar incidents by embedding distance; empty list when none.
- [x] Structured errors; typed; read-only.

## Outcome
Built `search_past_incidents` via memory.query: returns `SimilarIncident` list (id, service, created_at, root_cause, resolution, resolution_type, similarity, model_generated) or `ToolFailure`. Unverified label in field descriptions, docstrings, str/repr. Commit 765ec48. Files: models/tools.py, tools/incident_search.py, models/memory.py, memory/episodic.py, tests.
