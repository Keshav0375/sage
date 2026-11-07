---
key: "E6-T5"
title: "Silver transform: Docling parse, Presidio scrub, chunking"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T1", "E6-T3"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "decision-logs.md#adr-014", "decision-logs.md#adr-009", "decision-logs.md#adr-016", "decision-logs.md#adr-027"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 159, "id": 6263518931, "url": "https://github.com/Keshav0375/FinAdvisor/issues/159"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Implement the pure silver transform that turns a bronze document into redacted, structure-aware chunks carrying the fields of the chunk identity.

## Description
Arch (4.7 `silver`): 'Docling parse, Presidio scrub, structure-aware chunking (256-512-token children, ~1k-token parents, token counts from Voyage `count_tokens`)'. Build `etl/silver/transform.py`: `transform(doc_bytes, doc_meta) -> list[Chunk]` where Chunk has `kind` (child|parent), `chunk_index`, `parent_ref`, `content` (redacted), `provision_path` (the structural path: section path of the document), `token_count`, `chunk_hash` (sha256 of the redacted content plus provision_path, stable across runs), `context_header`, plus ACL fields copied from the document (`tier_required, jurisdiction, regulatory_ref, last_reviewed_at, source_title`).

Round 4 (ADR-027, ADR-016 amended, deep-dive 05-1 §5.10): (1) The chunk identity is the unique 8-column key `(tenant_id, document_id, provision_path, chunk_index, chunk_hash, valid_from, parser_version, embed_model)`; the transform therefore takes `valid_from` (from `doc_meta`, the version's start of validity) and `parser_version` (a constant bumped when the parser or chunker changes) and stamps both on every Chunk; `chunk_hash` does NOT include them (so unchanged text keeps its hash across versions and parser bumps and vectors can be reused). (2) Baseline B0 (ADR-016 amended): the chunker writes the free structural prefix, 'title plus section path', into `context_header` for every child chunk; contextual headers from Haiku are an ablation arm and OFF by default. (3) Presidio runs English only; no DE/FR PII claim is made (the E4-T2 spike measures it). Scrub before anything is written. Use the chunk-size findings and Docling version from docs/adr/docling-497k.md. Voyage `count_tokens` is called through an injectable client. Out of scope: Pandera, Parquet, Kafka (E6-T6/T7), Haiku headers (E6-T8).

## Acceptance criteria
- [ ] Given the planted-PII manifest from E6-T3, when a document is transformed, then no planted PII string appears in any chunk content (test).
- [ ] Given a doc, when transformed twice, then the chunk_hash list is identical; given the same doc with a bumped `parser_version`, the chunk_hash list is still identical but every Chunk carries the new parser_version and the given `valid_from` (test_chunk_identity_fields).
- [ ] Given a child chunk, when its `context_header` is read, then it equals 'title > section path' of its provision (B0 structural prefix) and contains no LLM-generated text (test).
- [ ] Child chunks have token_count in 256..512 except a final short chunk per section; parents <= 1100 (property test over the synthetic corpus); each child references a parent present in the output.
