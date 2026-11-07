---
key: "E4-T11"
title: "CitationVerifier implementation and server citation events"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E3-T14", "E4-T8"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.2", "decision-logs.md#ADR-009", "deep-dive/08-security-and-privacy.md#8.1"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 103, "id": 6155690755, "url": "https://github.com/Keshav0375/FinAdvisor/issues/103"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Deterministic verifier: every [n] in retrieved chunk ids with quote overlap; server emits citation events.

## Description
Implement the CitationVerifier Protocol defined in E3 (the cache hit path in E3-T14 already depends on it). Rules (ADR-009, 8.1 LLM05): every [n] in the answer maps to a retrieved chunk of this turn (id set from the retrieval result); a cited claim must overlap the chunk text by a deterministic quote/token-overlap threshold (threshold a config value tuned in evals, default documented). On accept, build the SSE 'citation' event {index, chunk_id, source_title, regulatory_ref, last_reviewed_at, stale, excerpt}; excerpt passes through the output redactor (G-16); stale is computed server-side. The model never emits citation events itself. Verifier failure behaviour: drop the uncited sentence marker and set finish_reason accordingly or return refusal; choose per arch (see questions). Uses retrieval.fetch_chunks(ids) for chunk data.

## Acceptance criteria
- [ ] Given an answer citing [4] when retrieved ids map only to 1..3, when verified, then it is rejected and no citation event is emitted (verifier test).
- [ ] Given an answer whose [n] set is a subset of retrieved chunks and with quote overlap above threshold, when verified, then one citation event per distinct n is returned with a redacted excerpt.
- [ ] Given a chunk excerpt containing an email, when the event is built, then the excerpt contains no email (test).
- [ ] Property test: for random answers, every [n] present in emitted citation events is in the retrieved chunk-id set.
