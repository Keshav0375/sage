---
key: "E6-T5"
title: "Silver transform: Docling parse, Presidio scrub, chunking"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T1", "E6-T3"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "decision-logs.md#adr-014", "decision-logs.md#adr-009"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Implement the pure silver transform that turns a bronze document into redacted structure-aware chunks with token counts.

## Description
Arch (4.7 `silver`): 'Docling parse, Presidio scrub, structure-aware chunking (256-512-token children, ~1k-token parents, token counts from Voyage `count_tokens`)'. Build `etl/silver/transform.py`: `transform(doc_bytes, doc_meta) -> list[Chunk]` where Chunk has `kind` (child|parent), `chunk_index`, `parent_ref`, `content` (redacted), `section_path`, `token_count`, `chunk_hash` (sha256 of the redacted content plus section_path, stable across runs), plus ACL fields copied from the document (`tier_required, jurisdiction, regulatory_ref, last_reviewed_at, source_title`). Scrub with Presidio before anything is written (reuse `backend/src/pii/redactor.py` where it fits; pseudonymization is in-process, ADR-009). Use the chunk-size findings and Docling version from docs/adr/docling-497k.md. Voyage `count_tokens` is called through a thin injectable client so tests can fake it. Out of scope: Pandera, Parquet and Kafka (E6-T6/T7), headers (E6-T8).

## Acceptance criteria
- [ ] Given the planted-PII manifest from E6-T3, when a document is transformed, then no planted PII string appears in any chunk content (test)
- [ ] Given a doc, when transformed twice, then the chunk_hash list is identical (test)
- [ ] Child chunks have token_count in 256..512 except a final short chunk per section; parents <= 1100 (property test over the synthetic corpus)
- [ ] Each child references a parent present in the output (test)
