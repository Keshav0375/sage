---
key: "E4-T11"
title: "CitationVerifier with original-text compare and as-of check"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E3-T14", "E4-T8"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/06-interfaces-and-contracts.md#6.10", "decision-logs.md#adr-009", "decision-logs.md#adr-027", "decision-logs.md#adr-036"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 103, "id": 6155690755, "url": "https://github.com/Keshav0375/FinAdvisor/issues/103"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Deterministic verifier: every [n] in retrieved chunk ids with quote overlap on the original chunk text, and every cited chunk valid at as_of.

## Description
Implement the CitationVerifier Protocol defined in E3 (the cache hit path in E3-T14 depends on it). Rules (ADR-009, 8.1 LLM05): every [n] maps to a retrieved chunk of this turn; a cited claim must overlap the chunk text by a deterministic quote/token-overlap threshold (config value, default documented). Round 4: (1) the overlap is computed against the ORIGINAL chunk text fetched by id with `retrieval.fetch_chunks(ids)`, never the model-visible JSON copy (ADR-036: 'citation verifier and numeric gate compare against the original chunk text fetched by id'); (2) as-of validity (ADR-027, 6.10): the verifier takes `as_of` (the date resolved by E4-T18) and, after generation, every cited chunk must satisfy `valid_range @> as_of` (half-open) or the release is blocked with `ANSWER_WITHHELD` reason `as_of_violation`; the same check runs on a cache-hit answer. On accept, build the SSE 'citation' event {index, chunk_id, source_title, regulatory_ref, jurisdiction, last_reviewed_at, stale, excerpt}; excerpt passes the output redactor (G-16); stale is computed server-side. The model never emits citation events. Verifier failure: drop the uncited sentence marker and set finish_reason, or refuse (decision in questions). Out of scope: resolving as_of (E4-T18), the numeric gate (E4-T28).

## Acceptance criteria
- [ ] Given an answer citing [4] when retrieved ids map only to 1..3, when verified, then it is rejected and no citation event is emitted (verifier test).
- [ ] Given a chunk whose model-visible copy was altered but whose stored text differs, when the claim overlaps only the altered copy, then verification fails (test_verifier_uses_original_text_by_id).
- [ ] Given a cited chunk with valid_range [2020-01-01, 2023-01-01) and as_of 2023-01-01 (boundary), when verified, then release is blocked with reason as_of_violation; with as_of 2022-12-31 it passes (test_post_generation_valid_range_check, also on a cache-hit answer).
- [ ] Given a chunk excerpt containing an email, when the event is built, then the excerpt contains no email (test).
- [ ] Property test: for random answers, every [n] present in emitted citation events is in the retrieved chunk-id set.
