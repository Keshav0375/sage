---
key: "E4-T18"
title: "Orchestrator pre-LLM stages: as_of, cache, screen+embed, gate"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T9", "E4-T10", "E4-T17", "E4-T13", "E3-T9", "E3-T14", "E3-T13", "E1-T14"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/06-interfaces-and-contracts.md#6.10", "decision-logs.md#adr-007", "decision-logs.md#adr-027", "decision-logs.md#adr-036"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Retrieve-first pipeline up to the gate, with the deterministic as_of resolver, the meta event and the refusal path.

## Description
src/agent orchestrator order (04 §4.5, Flow 1): guard-in (cap, Presidio) -> condensation (if history) -> `as_of` resolve -> answer_cache lookup (E3-T13/T14; the key now includes `as_of`, `embed_model`, `source_epoch`; a hit re-fetches via fetch_chunks, re-runs the CitationVerifier incl. the as-of check, and is a miss on an invisible chunk) -> on miss: E4-T9 screen in parallel with Voyage embed -> RetrievalService search+rerank+gate (E3, takes `as_of`) -> emit `meta` {retrieval_degraded, reason?, as_of, as_of_source} once after rerank and store messages.retrieval_degraded. Gate failure emits 'refusal' {NO_FIRM_DOCUMENTATION, escalate_offer} then done(gate) with no LLM call. A cache hit emits delta/citation events from the verified answer and skips screen and embed. Failures map to one error event with a code.

As-of resolver (ADR-027, 6.10, R4-D4, R4-D20 E11-Q2): `agent/as_of.py` deterministic parser, NEVER the model, no tool accepts `as_of`. Order: an explicit date or year found in the question by the parser; else the optional `as_of` (ISO date) of `POST /v1/chat` set by the UI chip; else the Postgres `SELECT (now() AT TIME ZONE 'utc')::date`. ISO 8601 is always accepted; numeric `DD/MM/YYYY` vs `MM/DD/YYYY` follows the advisor's jurisdiction from the Principal (US month-first, EU and UK day-first); ambiguity is never resolved by the model. `as_of_source` is `parsed`, `chip` or `today`. The server emits a `notice {kind:"as_of", text}` (server text, not model text) so the answer echoes the parsed date. When retrieval signals `no_version_history` (UK sources before the first observation; produced by E11-T24) the orchestrator emits `refusal {ANSWER_WITHHELD, reason: no_version_history}` and makes zero LLM calls. Out of scope: the post-generation check (E4-T11), numeric gate (E4-T28), the known_at helper (E11-T24).

## Acceptance criteria
- [ ] Given the question date `03/04/2024`, when resolved, then a US advisor gets 2024-03-04 and a UK advisor gets 2024-04-03, and ISO `2024-04-03` resolves the same for both (tests test_ambiguous_date_us_advisor, test_ambiguous_date_uk_advisor, test_iso_always_accepted).
- [ ] Given a question with no date, a UI chip date and no chip, when resolved, then as_of_source is `parsed`, `chip` and `today` in that precedence, today = the DB date in UTC even when the app clock is shifted 2 h (test); the LLM stub is never asked for a date.
- [ ] Given a turn, when events are captured, then `meta` carries as_of and as_of_source and a `notice` of kind as_of states the same date; the as_of is part of the cache key lookup (E3-T13 stub asserts the argument).
- [ ] Given the gate stub failing, when a turn runs, then events are turn, meta, refusal, done(gate) and the LLM stub is called 0 times; given retrieval signalling no_version_history, then refusal reason is no_version_history and LLM calls are 0.
- [ ] Given the reranker stub returning 429, then meta.retrieval_degraded is true with reason rerank_429 and the stored messages.retrieval_degraded is true; given a cache hit, Model Armor and Voyage stubs are called 0 times and a hit citing an invisible chunk behaves as a miss.
