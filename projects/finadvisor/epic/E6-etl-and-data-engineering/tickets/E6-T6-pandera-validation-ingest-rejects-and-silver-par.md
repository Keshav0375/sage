---
key: "E6-T6"
title: "Pandera validation, ingest_rejects and silver Parquet"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T5", "E1-T5", "E1-T8"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/05-data-model-and-storage.md#5.8", "decision-logs.md#adr-014"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Validate chunks with Pandera, route failures to ingest_rejects and write redacted silver Parquet partitioned by tenant and date.

## Description
Arch (4.7 `silver`, 5.2 `ingest_rejects`, 5.8): 'Pandera validation, rejects to `ingest_rejects`, writes silver Parquet to the data bucket under `silver/tenant_id=<id>/dt=<date>/`'. `ingest_rejects` columns: `(tenant_id, id)`, `document_id`, `bronze_sha256`, `stage`, `rule` (Pandera check), `detail` (redacted), `created_at`. Define a Pandera schema `ChunkSchema` (non-empty content, token_count within bounds, tier_required 1..4, jurisdiction in US/EU/UK, chunk_hash 64 hex, valid parent link, content free of detected PII entities via a re-scan). A failing row never goes to Parquet; one `ingest_rejects` row is written per failed check with `detail` redacted (no raw content) and the document-level outcome recorded. Write passing chunks as Parquet to `silver/tenant_id=<id>/dt=<date>/<document_id>.parquet`. Out of scope: consumer wiring (E6-T7).

## Acceptance criteria
- [ ] Given a chunk set with 3 deliberately invalid rows (empty content, tier 9, bad jurisdiction), when validated, then `ingest_rejects` gains exactly 3 rows with `rule` naming each check and none appear in the Parquet (test)
- [ ] Given a rejected row, when `detail` is inspected, then it contains no substring of the original content longer than 20 chars (test)
- [ ] Parquet path matches `silver/tenant_id=<id>/dt=<date>/` and a reader recovers the same chunk_hash set (test)
- [ ] Re-running the same document writes the same Parquet object path without duplicating reject rows (unique-by-rule test)
