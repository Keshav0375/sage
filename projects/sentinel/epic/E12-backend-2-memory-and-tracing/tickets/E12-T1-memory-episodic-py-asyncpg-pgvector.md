---
key: "E12-T1"
title: "memory/episodic.py (asyncpg + pgvector)"
epic: "E12"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E11-T2", "E12-T3"]
arch_refs: ["deep-dive/05-data-and-memory.md#5.1", "deep-dive/00-poc-and-the-pivot-to-mvp.md#0.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 55, "id": 5694996543, "url": "https://github.com/Keshav0375/sentinel-brain/issues/55"}
branch: "dev/backend-phase-2-memory-and-tracing"
pr: "https://github.com/Keshav0375/Sentinel/pull/20"
updated: "2026-11-08"
---

## Summary
Rewrite episodic memory to asyncpg + pgvector, keeping the existing `MemoryStore` protocol

## Description
Source: backend task 2.1 (`sentinel-brain/implementation/tasks/backend/phase-2-memory-and-tracing/task-1-episodic-memory.md`).

(`memory/base.py`) — same interface, new implementation (§13.2).

**Files modified:** `src/sentinel/memory/episodic.py`
- `store_incident(...)` → INSERT into `incidents` (trajectory JSONB, embedding VECTOR(384), all correlation fields, mttr, reflexion_loops).
- `search_similar(embedding, k)` → `ORDER BY embedding <=> $1 LIMIT k` (ivfflat).
- `get(incident_id)`, `list(status/service filters)`.
- Provenance preserved (which incident/agent) per safety invariant.

## Acceptance criteria
- [x] Implements the `MemoryStore` protocol unchanged; all methods async + typed.
- [x] Similarity search uses the pgvector `<=>` operator (not numpy scan).
- [x] Round-trips a full incident row incl. trajectory + embedding.

## Outcome
Commit `fa71aa7` (refactor: episodic memory on asyncpg + pgvector) on `dev/backend-phase-2-memory-and-tracing`.
EpisodicMemory(pool | None, embedding_client); pool None raises SentinelMemoryError on every method. Incident ids are str(uuid4()); trajectory = {symptoms, timeline}; similarity via `<=>` under SET LOCAL ivfflat.probes=10, no numpy. Added search_by_embedding (MemoryQueryResult) and list_incidents(status, service, limit). incident_search reports "memory unavailable" instead of crashing. resolved_at written when the model has it.
Files: src/sentinel/memory/episodic.py, memory/short_term.py, tools/incident_search.py, tools/registry.py, main.py, eval/runner.py, scripts/run_scenario.py, models/incident.py, api/webhooks.py, plus tests (test_episodic, test_incident_search, test_runner, test_triage, test_registry, test_incident, test_webhooks).
