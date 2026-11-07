---
key: "E6-T10"
title: "indexer: hash-gated embed, upsert, supersede, corpus_version"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T8", "E3-T3", "E3-T4", "E1-T8"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/04-1-key-flows.md#4.14", "deep-dive/05-data-model-and-storage.md#5.2", "decision-logs.md#adr-014"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Implement the indexer role that embeds only new (tenant_id, chunk_hash, embed_model) chunks and bumps corpus_version.

## Description
Arch (4.7 `indexer`; Flow 2; 5.2 `chunks`): 'consumes `chunks.contextualized.v1`: Voyage `voyage-4` document embeddings only for chunks whose `(tenant_id, chunk_hash, embed_model)` is new, upserts `chunks`, deletes superseded chunks, then bumps the tenant's `corpus_version` (UPDATE on its own tenant row by policy), emits `chunks.indexed.v1`.' Use `EMBED_MODEL`/`EMBED_DIM` (voyage-4, 1024) and the E3-T3 embeddings client with `input_type='document'`. Per message in one transaction with `processed_events`: look up existing `(chunk_hash, embed_model)`; embed only the missing children (parents have NULL embedding); upsert with unique `(tenant_id, chunk_hash, embed_model)` (`ON CONFLICT DO UPDATE` of ACL/metadata columns only, no re-embed); delete chunks of the document not in the new hash set; `UPDATE tenants SET corpus_version = corpus_version + 1` only if anything changed. Embedding calls batched. Runs as `fa_worker`. Out of scope: columns/indexes (E3-T4).

## Acceptance criteria
- [ ] Given a document ingested once, when the identical message is processed again, then the Voyage fake records 0 embed calls, `chunks` row count is unchanged and `corpus_version` is unchanged (test, count asserted)
- [ ] Given a document with one paragraph edited, when reprocessed, then exactly the changed children are embedded and the superseded chunk rows are deleted (test asserts the embed call input count)
- [ ] Given a first ingest, when processed, then `tenants.corpus_version` increases by exactly 1 per message with changes (test)
- [ ] Given `fa_worker` in tenant A context, when it writes a chunk with tenant B id, then RLS denies it (test)
