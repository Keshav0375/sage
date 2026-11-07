---
key: "E3-T4"
title: "Migration: halfvec, FTS and HNSW indexes on chunks"
epic: "E3"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E1-T21", "E3-T2"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/05-data-model-and-storage.md#5.5", "deep-dive/05-data-model-and-storage.md#5.3", "decision-logs.md#adr-008"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 64, "id": 6155646156, "url": "https://github.com/Keshav0375/FinAdvisor/issues/64"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Make the chunks table carry halfvec(1024), a generated tsvector, HNSW and GIN indexes per partition, replacing IVFFlat.

## Description
Alembic migration (run by the `migrate` job as `fa_owner`) that brings `chunks` to the retrieval shape. First check what the E1 baseline already created and add only what is missing; the migration must be idempotent against it and the onboarding path (`migrate --onboard-tenant`) must create the same indexes for a new tenant partition.

Arch (deep-dive/05-data-model-and-storage.md §5.2): "`embedding halfvec(1024)` (children only, NULL for parents), `tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple', coalesce(context_header,'') || ' ' || content)) STORED`". Overview §5.5: "Per partition, on `chunks`: HNSW on `embedding halfvec_cosine_ops` with `m = 16`, `ef_construction = 64`, partial `WHERE kind = 'child'`; GIN on `tsv`; btree `(tenant_id, document_id)`, `(tenant_id, parent_id)`, `(tenant_id, tier_required, jurisdiction)`; unique `(tenant_id, chunk_hash, embed_model)`" and "indexes are declared on the parent so each partition gets its own". The MVP IVFFlat index (`lists=10`, built on an empty table; G-34) is dropped. Use the `HNSW_EF_SEARCH` and per-leg values from the E3-T2 ADR only for documentation; index build parameters are fixed (m 16, ef_construction 64).

Constraints: no GRANT on partitions (deep-dive/05-data-model-and-storage.md §5.3); `fa_app` still has SELECT only. pgvector >= 0.8 (image `pgvector/pgvector:0.8.5-pg16`). Existing `vector(1024)` data is converted with a cast to `halfvec(1024)` (the MVP table is empty or re-ingested; no data migration script beyond the cast).

Out of scope: the answer_cache table (E3-T13), partition creation logic itself (E1), re-embedding existing rows with voyage-4 (E6 indexer).

## Acceptance criteria
- [ ] Given an empty database when `alembic upgrade head` runs then `\d+ chunks` shows `embedding halfvec(1024)` and generated `tsv`, and `pg_indexes` for each tenant partition lists one hnsw index with `m='16', ef_construction='64'` and `WHERE kind = 'child'`, one gin index on `tsv` and the three btree indexes (test `backend/tests/test_migration_chunks_indexes.py::test_indexes_on_every_partition`).
- [ ] Given the migration is run twice then the second run changes nothing (test `test_migration_idempotent`).
- [ ] Given `migrate --onboard-tenant` creates a new tenant partition then that partition has the HNSW and GIN indexes without an extra call (test `test_onboarded_partition_has_indexes`).
- [ ] `pg_indexes` contains no `ivfflat` index on `chunks`, and the partitions carry no grants to `fa_app` or `fa_worker` (test `test_no_ivfflat_no_partition_grants`).
