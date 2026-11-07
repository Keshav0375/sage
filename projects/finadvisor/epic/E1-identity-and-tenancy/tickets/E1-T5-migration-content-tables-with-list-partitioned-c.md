---
key: "E1-T5"
title: "Migration: content tables with LIST-partitioned chunks"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T2", "E1-T4"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.5", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.10", "decision-logs.md#adr-003", "decision-logs.md#adr-027", "decision-logs.md#adr-035"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 21, "id": 6155593763, "url": "https://github.com/Keshav0375/FinAdvisor/issues/21"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
documents, chunks (LIST by tenant), suitability_rules and ingest_rejects exist in the target shape with composite FKs, raw_content dropped, and the PUBLIC and DEFAULT partitions.

## Description
Add an Alembic revision (0002 or later; baseline 0001 is immutable) as `fa_owner` that replaces the MVP content tables with the target shape of deep-dive/05-data-model-and-storage.md §5.2 and 5.5. The MVP `documents.raw_content` column is dropped (G-03: "No `raw_content` column"). The service has never been deployed, so the revision drops and recreates the MVP content tables without a data migration.

Tables, all `FORCE` + `ENABLE` RLS at creation, all with `tenant_id uuid NOT NULL`:
- `documents (tenant_id, id)`: columns per 5.2 (`title, doc_type, jurisdiction, tier_required CHECK 1..4, regulatory_ref, last_reviewed_at, product_category, risk_level, source CHECK in (edgar, synthetic), source_uri, bronze_uri, bronze_sha256, parser_version, status CHECK in (active, superseded, deleted), created_at`); unique `(tenant_id, bronze_sha256)`; index `(tenant_id, doc_type, jurisdiction)`.
- `chunks (tenant_id, id)` `PARTITION BY LIST (tenant_id)`; columns per 5.2 including `embedding halfvec(1024)` and `tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple', coalesce(context_header,'') || ' ' || content)) STORED`; composite FKs `(tenant_id, document_id)` to documents and `(tenant_id, parent_id)` self; identity unique `(tenant_id, document_id, provision_path, chunk_index, chunk_hash, valid_from, parser_version, embed_model)` (round 4, below). Indexes declared on the parent so each partition gets its own: HNSW on `embedding halfvec_cosine_ops` `m=16, ef_construction=64` partial `WHERE kind = 'child'`; GIN on `tsv`; btree `(tenant_id, document_id)`, `(tenant_id, parent_id)`, `(tenant_id, tier_required, jurisdiction)`.
- `suitability_rules (tenant_id, id)`: per 5.2, composite FK `(tenant_id, source_document_id)`, `client_risk_profile` CHECK 3 values (use the values already in the MVP schema).
- `ingest_rejects (tenant_id, id)`: per 5.2.
Partitions: one for the PUBLIC tenant (`chunks_public`) and a DEFAULT partition (`chunks_default`); rows in DEFAULT are a bug. Write a reusable function `src/db/partitions.create_chunks_partition(conn, tenant_id)` (partition name from the uuid, no `GRANT`) that E1-T11 reuses. The partitions are created without any grants.

If E1-T2's ADR changed the partition design, follow the ADR.

Out of scope: policies and grants (E1-T8), tenant partitions (E1-T11), changing the retrieval code that reads these tables (E3).

Round 4 (ADR-027, ADR-035, R4-D3, R4-D19 M1; deep-dive/05-1 section 5.10): (1) `CREATE EXTENSION IF NOT EXISTS btree_gist` first, as `fa_owner`. Availability on Cloud SQL PostgreSQL 16 is UNVERIFIED: the migration fails with a clear message if the extension cannot be created, and the PR records the check on a Cloud SQL instance (or marks it open for E10). (2) `chunks` also carries `provision_path`, `chunk_index`, `kind`, `valid_from date NOT NULL`, `parser_version`, `embed_model`, `valid_range daterange NOT NULL`, `system_range tstzrange NOT NULL`, `is_current boolean GENERATED ALWAYS AS (upper_inf(valid_range)) STORED`, with CHECK `valid_from = lower(valid_range)`. The identity above is UNIQUE (it includes `embed_model`, so generations coexist); the old `(tenant_id, chunk_hash, embed_model)` becomes a plain, non-unique index used to reuse vectors. (3) `create_chunks_partition(conn, tenant_id)` also executes, for the leaf it creates (the PUBLIC partition migration does the same for `chunks_public`), `ALTER TABLE chunks_<tenant> ADD CONSTRAINT chunks_<tenant>_no_overlap EXCLUDE USING gist (tenant_id WITH =, document_id WITH =, provision_path WITH =, chunk_index WITH =, kind WITH =, embed_model WITH =, valid_range WITH &&) WHERE (upper_inf(system_range))`. PostgreSQL 16 cannot declare an exclusion constraint on a partitioned parent, hence per leaf. The composite FKs to `document_versions` and the `documents` column changes of section 5.2 belong to E11-T4/E11-T5 (that epic owns `document_versions`); not here.

## Acceptance criteria
- [ ] Given `alembic upgrade head` on an empty database, then `tests/db/test_schema_content.py` passes: `chunks` has `relkind='p'` and `partstrat='l'`, partitions `chunks_public` and `chunks_default` exist, and `documents` has no column named `raw_content`.
- [ ] Given a chunk row whose `(tenant_id, document_id)` points to a document of another tenant, when inserted as `fa_owner`, then it raises a ForeignKeyViolation (composite FK; test).
- [ ] Given `create_chunks_partition(conn, <uuid>)` is called, then a partition bound to that uuid exists and `has_table_privilege` for `fa_app`, `fa_worker`, `fa_etl`, `fa_etl_public` and `fa_dbt` on it is false for every privilege (test).
- [ ] Given two rows with the same full 8-column identity, then the second insert raises a UniqueViolation; given text A (valid 2020-01-01 to 2021-01-01), text B, then text A again with `valid_from` 2022-01-01, the three rows insert with disjoint ranges and no violation (A-B-A test `tests/db/test_chunk_identity.py::test_aba_is_three_rows`).
- [ ] Given the PUBLIC partition, then `pg_indexes` shows an HNSW index with `halfvec_cosine_ops`, `m='16'`, `ef_construction='64'` and predicate `kind = 'child'`, a GIN index on `tsv`, and a NON-unique index on `(tenant_id, chunk_hash, embed_model)` (`test_public_partition_indexes`).
- [ ] Given two current rows with the same `(tenant_id, document_id, provision_path, chunk_index, kind, embed_model)` and overlapping `valid_range`, when inserted into a leaf created by `create_chunks_partition`, then Postgres raises an exclusion violation (SQLSTATE 23P01); the same overlap with `system_range` closed (not `upper_inf`) is accepted; the same overlap with a different `embed_model` is accepted (`test_exclude_per_leaf`).
