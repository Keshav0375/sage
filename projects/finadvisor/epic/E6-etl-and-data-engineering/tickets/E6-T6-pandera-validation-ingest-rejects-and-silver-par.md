---
key: "E6-T6"
title: "Pandera validation, ingest_rejects and versioned silver Parquet"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T5", "E1-T5", "E1-T8"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.8", "decision-logs.md#adr-014", "decision-logs.md#adr-034"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 160, "id": 6263519897, "url": "https://github.com/Keshav0375/FinAdvisor/issues/160"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Validate chunks with Pandera at SCHEMA_AND_DATA depth, route failures to ingest_rejects and write silver Parquet under a per-document-version path.

## Description
Arch (4.7 `silver`, 5.2 `ingest_rejects`, 5.8): Pandera validation, rejects to `ingest_rejects`, silver Parquet in the data bucket. `ingest_rejects` columns: `(tenant_id, id)`, `document_id`, `bronze_sha256`, `stage`, `rule`, `detail` (redacted), `created_at`. Define `ChunkSchema` (non-empty content, token_count within bounds, tier_required 1..4, jurisdiction in US/EU/UK, chunk_hash 64 hex, valid parent link, non-null `valid_from` and `parser_version`, content free of detected PII entities via a re-scan). A failing row never goes to Parquet; one `ingest_rejects` row per failed check with `detail` redacted.

Round 4 (ADR-014 amended, ADR-034, 4.7): (1) Silver path is `silver/tenant_id=<id>/doc_id=<id>/version=<id>/` (one document version per file set, so one document is deletable by prefix), replacing `silver/tenant_id=/dt=/`; `version` is the document version id passed in `doc_meta`. (2) Validation runs with `PANDERA_VALIDATION_DEPTH=SCHEMA_AND_DATA` (a setting; the default in all environments is `SCHEMA_AND_DATA`; with `SCHEMA_ONLY` the test fails, because Pandera's default would skip data checks). (3) Dagster blocking checks are advisory only; the atomic indexer gate is the control, so this ticket sets `contract_passed` inputs but never relies on a Dagster check to stop a write. Out of scope: consumer wiring (E6-T7), contract rules (E11-T11).

## Acceptance criteria
- [ ] Given a chunk set with 3 deliberately invalid rows (empty content, tier 9, bad jurisdiction), when validated, then `ingest_rejects` gains exactly 3 rows with `rule` naming each check and none appear in the Parquet.
- [ ] Given a row failing only a DATA-level check (value out of range, schema type fine), when validated at the configured depth, then it is rejected; with depth forced to SCHEMA_ONLY the test asserts config load fails (test_pandera_depth_is_schema_and_data).
- [ ] Given a document version, when written, then the Parquet path matches `silver/tenant_id=<id>/doc_id=<id>/version=<id>/` and deleting that prefix removes every object of that version and no other (fake-gcs test).
- [ ] Given a rejected row, when `detail` is inspected, then it contains no substring of the original content longer than 20 chars; re-running the same version writes the same path without duplicating reject rows.
