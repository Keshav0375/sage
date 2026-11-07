---
key: "E6-T22"
title: "voyage-context-4 contextualized chunk embeddings as an eval-only generation"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T25", "E12-T26", "E6-T21"]
arch_refs: ["deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.6", "deep-dive/04-components-and-responsibilities.md#4.27", "deep-dive/02-quality-attributes.md#2.10", "decision-logs.md#adr-035", "decision-logs.md#adr-037", "decision-logs.md#adr-039"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Build an embedding generation with `voyage-context-4` contextualized chunk vectors for the eval tenant only, so ablation arm 2 can compare it with plain chunks.

## Description
Confirmatory arm 2 of ADR-037 is "`voyage-context-4` contextualized chunks vs plain chunks". The default pipeline stays on the plain-chunk model; this ticket produces the comparison data using the embedding-generation mechanism of E12 (`embed_generations`, partial HNSW per generation, `embed-backfill`, ADR-035: generations are unique on the 8-column chunk identity incl. `embed_model`).

Register `voyage-context-4` in the embed-model allow-list (5.6) and in `embed_generations` with status `building` then `validating`, never `active` (a CHECK or a test: `active_embed_model` is never `voyage-context-4` for any tenant). Extend the E12-T26 backfill with a model-specific embedder: Voyage contextualized embeddings take, per document, the ordered list of that document's chunks and return one vector per chunk (the document context is in the call, not in the stored text), so the embedder groups chunk texts by version in order and respects the model's per-request limits (read from the Voyage docs at implementation; record limits in the PR). Restrict the build to tenant `eval` (config `EVAL_CONTEXT_EMBED_TENANTS`, default the eval tenant); child chunk rows for the generation reuse chunk ids and text, only `embed_model` and the vector differ. The generation is queryable only by the eval runner (E7-T6 config `embed: voyage_context_4`, which sets the run's query-embedding model for that run); chat never queries it (`EmbedModelMismatch` of E12-T25 holds). Erasure and withdrawal delete by `doc_id` and therefore hit this generation too (E12-T9), and it is retired with the E12-T28 command. Private items: no private document is embedded with this model unless `llm_egress_ack` is true for that tenant (E11-T14).

Out of scope: validation and flip (E12-T27), the arm run and its statistics (E7-T7), changing the default model.

## Acceptance criteria
- [ ] Given the allow-list, when `voyage-context-4` is set as `tenants.active_embed_model` for any tenant, then the migration CHECK or the setter raises (test `test_context_embed.py::test_never_active`).
- [ ] Given a stub Voyage client and a 3-chunk document, when the embedder runs, then it makes one contextualized call with the 3 chunk texts in order and stores 3 vectors under `embed_model = 'voyage-context-4'` with the same chunk ids as the plain generation (test `test_context_embed.py::test_one_call_per_document_in_order`).
- [ ] Given tenants `eval` and `firm-a`, when the backfill runs with the default setting, then rows exist only for `eval` (test `test_context_embed.py::test_eval_tenant_only`).
- [ ] Given a chat request, when retrieval runs, then it never reads `voyage-context-4` rows (the query asserts the active model literal) and an eval query with `embed: voyage_context_4` does (test `test_context_embed.py::test_chat_never_queries_generation`).
- [ ] Given an erasure of a document embedded in both generations, when the E12-T9 delete runs, then zero chunk rows remain for either model (test `test_context_embed.py::test_erasure_hits_both_generations`).
