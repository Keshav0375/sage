---
key: "E3-T3"
title: "Voyage embeddings: voyage-4 with query/document input_type"
epic: "E3"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E0-T14"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.6", "decision-logs.md#adr-008"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 63, "id": 6155645020, "url": "https://github.com/Keshav0375/FinAdvisor/issues/63"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Replace the voyage-3 document-typed query embedding with an async voyage-4 client that uses the correct input_type.

## Description
Rewrite `backend/src/retrieval/embeddings.py` (as built: voyage-3, queries embedded with `input_type="document"`, sync SDK via threads; G-33, G-36).

Arch (ADR-008): "Voyage `voyage-4` with `input_type` query / document; `halfvec(1024)`". Config §6.6: `EMBED_MODEL` = `voyage-4`, `EMBED_DIM` = 1024, `VOYAGE_API_KEY` required. Stack: "Voyage `voyage-4` (1024 dims, `input_type` query / document) | model id from config; voyageai SDK pin at implementation" - pin the voyageai SDK in the lockfile in this ticket and update deep-dive/11-tech-stack.md's version cell. G-36 is accepted as a single provider: no second embedding provider, no fallback.

Interfaces (module `retrieval.embeddings`, async, using the voyageai async client; model id and dim only from `Settings`):
- `embed_query(text: str) -> list[float]` calls Voyage with `input_type="query"`.
- `embed_documents(texts: list[str]) -> list[list[float]]` calls with `input_type="document"` (used by the indexer in E6; batch size limited by the Voyage per-request cap).
- Both raise a typed `EmbeddingError` (no provider text in the message) on timeout or API error, with an explicit client timeout from config; assert returned dimension == `EMBED_DIM`.
Texts passed in are assumed already PII-redacted by the caller (guardrails, E4); this module does not redact.

Out of scope: retries/circuit breaker beyond a single explicit timeout (arch is silent; see questions), batching policy for the indexer (E6), a fallback provider.

## Acceptance criteria
- [ ] Given a stubbed Voyage client when `embed_query('x')` is called then the client received `input_type='query'` and model `voyage-4`; when `embed_documents(['x'])` is called then it received `input_type='document'` (test `backend/tests/test_embeddings.py::test_input_types`).
- [ ] Given the stub returns a 512-dim vector when `embed_query` runs then `EmbeddingError` is raised (test `test_dimension_mismatch`).
- [ ] Given the stub raises a timeout when `embed_query` runs then `EmbeddingError` is raised and its message contains no API key or provider response text (test `test_error_is_redacted`).
- [ ] `grep -rn 'voyage-3' backend/src` returns no match, and the model id appears only in `Settings` defaults (CI step `test_no_hardcoded_embed_model`).
