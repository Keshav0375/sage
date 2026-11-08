---
key: "E21-T1"
title: "Agent checkpoints, tool/LLM cache, Redis-backed short-term memory"
epic: "E21"
repo: "Sentinel"
size: "M"
status: "done"
depends_on: []
arch_refs: ["deep-dive/05-data-and-memory.md#5.5", "deep-dive/12-evaluation.md#12.3"]
issue: null
branch: "dev/backend-phase-11-memory-hardening"
pr: "https://github.com/Keshav0375/Sentinel/pull/35"
updated: "2026-11-08"
---

## Summary
Migration 003 adds `incident_checkpoints` and `cache_entries`.

## Description
Source: backend task 11.1 (built in https://github.com/Keshav0375/Sentinel/pull/35).

Migration 003 adds `incident_checkpoints` and `cache_entries`. An in-flight incident resumes once after a restart with every cap carried over (per-call tool budget, absolute reflexion and wall-clock deadline). Cache: `fetch_logs` always, deterministic LLM calls behind a flag, the judge never. Redis-backed STM with an in-process fallback; status pub/sub.

## Acceptance criteria
- [x] A restarted pod resumes an in-progress incident at most once
- [x] Resumed runs cannot exceed the original tool-call budget or deadline
- [x] The judge is never served from cache

## Outcome
Merged in https://github.com/Keshav0375/Sentinel/pull/35 on 2026-10-30.
