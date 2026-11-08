---
key: "E12-T2"
title: "memory/semantic.py (asyncpg)"
epic: "E12"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E11-T2", "E11-T4"]
arch_refs: ["deep-dive/05-data-and-memory.md#5.1", "deep-dive/00-poc-and-the-pivot-to-mvp.md#0.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 56, "id": 5694996658, "url": "https://github.com/Keshav0375/sentinel-brain/issues/56"}
branch: "dev/backend-phase-2-memory-and-tracing"
pr: "https://github.com/Keshav0375/Sentinel/pull/20"
updated: "2026-11-08"
---

## Summary
Rewrite semantic (service registry) memory to asyncpg PostgreSQL queries; same protocol.

## Description
Source: backend task 2.2 (`sentinel-brain/implementation/tasks/backend/phase-2-memory-and-tracing/task-2-semantic-memory.md`).

**Files modified:** `src/sentinel/memory/semantic.py`
- `get_service(name)` → row from `services`.
- `search_services(embedding, k)` → pgvector similarity ("which service matches this symptom?").
- Typed dataclass/Pydantic return; async.

## Acceptance criteria
- [x] Lookup-by-name + similarity search implemented against `services`.
- [x] Protocol-compatible; no LLM call for lookup.

## Outcome
Commit 3c8f2de `refactor: semantic memory on asyncpg + pgvector` (Sentinel).
Files: src/sentinel/memory/semantic.py, tools/service_lookup.py, main.py, eval/runner.py, scripts/run_scenario.py, tools/registry.py, models/{memory,service}.py (docstrings), tests (test_semantic, test_service_lookup, test_registry, test_triage, test_log_analyst, test_runner).
SemanticMemory(pool | None): pool None raises SentinelMemoryError; missing service is KeyError. Exact name lookup; search_services under SET LOCAL ivfflat.probes=5. metadata JSONB fills oncall_channel/description/repo_url; services.runbook parsed into ordered steps. Edge choices: store/delete stay NotImplementedError; NULL team -> "", invalid tier raises SentinelMemoryError; blank runbook = NULL.
Known: eval/run_scenario scenarios still name POC acme services (lookups "not found") until phase 4. Boot proven both ways.
