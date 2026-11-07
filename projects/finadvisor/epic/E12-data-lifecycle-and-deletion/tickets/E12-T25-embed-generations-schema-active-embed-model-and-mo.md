---
key: "E12-T25"
title: "embed_generations schema, active_embed_model and model allow-list"
epic: "E12"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E3-T4", "E1-T4"]
arch_refs: ["deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.10", "deep-dive/04-2-source-lifecycle-and-cells.md#4.27", "decision-logs.md#adr-35", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#19"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add embed_generations, tenants.active_embed_model and the per-model query path with a wrong-model guard.

## Description
Create `embed_generations(model_id PK, status in (building, validating, active, retired))` as global reference data (no tenant_id; written only by migrations; SELECT to every runtime role) and `tenants.active_embed_model`. The HNSW index is partial per generation (`WHERE kind = 'child' AND embed_model = '<model>'`) and the migration creates it for the active model; queries inline the model literal from the allow-list (5.6) and assert the query embedding's model equals `active_embed_model`, else raise `EmbedModelMismatch`. A half-built (`building`) generation is invisible to queries. Cache key already includes `embed_model` (5.7). Out of scope: the backfill, validation and flip.

## Acceptance criteria
- [ ] Given green rows in `building` and blue `active`, when a query runs for a tenant, then results come from blue only (#19).
- [ ] Given a query embedded with a model other than the tenant's `active_embed_model`, then `EmbedModelMismatch` is raised and no SQL is executed (#19).
- [ ] Given a model id not in the allow-list, then the query builder refuses it (SQL-injection-safe literal test).
- [ ] Given `fa_app`, when it INSERTs into `embed_generations`, then permission is denied.
