---
key: "E6-T21"
title: "indexer embed stage: chunk identity and vector reuse"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T8", "E3-T3", "E3-T4", "E1-T8"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.10", "decision-logs.md#adr-035", "decision-logs.md#adr-027", "decision-logs.md#adr-039"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 155, "id": 6263515073, "url": "https://github.com/Keshav0375/FinAdvisor/issues/155"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Embed only chunks whose vector is missing, outside any transaction, and hand a publish plan keyed on the 8-column chunk identity to the publisher.

## Description
Implement the embed half of the `indexer` role (04 §4.7: 'Embeds with Voyage `voyage-4` outside any transaction (vectors reused by the non-unique `(tenant_id, chunk_hash, embed_model)` index; chunk identity is the 8-column key of §5.10)'). Round 4 (R4-D19 M1, ADR-035 amended, 05-1 §5.10): the identity is the unique key `(tenant_id, document_id, provision_path, chunk_index, chunk_hash, valid_from, parser_version, embed_model)`; embedding generations are unique on that identity (it includes `embed_model`), so a green generation row for a new model is a different row for the same chunk. `(tenant_id, chunk_hash, embed_model)` is only a plain reuse index, NOT a unique constraint, because a unique 3-column key would make text A, then B, then A impossible.

Per `chunks.contextualized.v1` message: read the silver Parquet; for each child compute its identity with the tenant's active `EMBED_MODEL` (default voyage-4, 1024 dims; `input_type='document'`; E3-T3 client, batched); look up vectors by the reuse index; embed ONLY children with no existing vector for `(tenant_id, chunk_hash, embed_model)`; parents have NULL embedding. No transaction is open during Voyage calls. Output a `PublishPlan {rows with vectors, reused-vector references, identities}` for E6-T10, never writing `chunks` itself. A parser bump with unchanged hashes costs zero embed calls (vectors are reused for the new `parser_version` rows); A-B-A text yields two rows with disjoint `valid_from`. Dual write while a generation is building is E12-T26. Out of scope: the transaction (E6-T10), generations lifecycle (E12).

## Acceptance criteria
- [ ] Given a document ingested once, when the identical message is processed again, then the Voyage fake records 0 embed calls and the plan has 0 new vectors (count asserted).
- [ ] Given a document with one paragraph edited, when planned, then exactly the changed children are embedded (embed input count == number of changed children).
- [ ] Given the same text A, then B, then A again over three versions, when planned, then three distinct identities exist with distinct `valid_from` and the third reuses the vector of A with 0 embed calls (test_aba_text_representable).
- [ ] Given a bumped parser_version with unchanged chunk hashes, when planned, then identities differ only in parser_version and embed calls are 0 (test_parser_bump_reuses_vectors).
- [ ] Given the Voyage client stub, when a plan is built, then no database transaction is open during any embed call (test asserting connection state inside the stub).
