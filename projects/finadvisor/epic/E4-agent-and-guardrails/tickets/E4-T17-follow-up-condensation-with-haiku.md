---
key: "E4-T17"
title: "Follow-up condensation with Haiku"
epic: "E4"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E4-T5", "E4-T16", "E4-T8"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#ADR-007", "decision-logs.md#ADR-006"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 109, "id": 6155697843, "url": "https://github.com/Keshav0375/FinAdvisor/issues/109"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Rewrite a follow-up into a standalone query only when history exists.

## Description
When history is non-empty, call LLMClient with LLM_MODEL_AUX (claude-haiku-5-5), small max_tokens, input = redacted history + redacted question, output = standalone redacted question used for embed/retrieval/cache key. No history -> no call. Failure or timeout falls back to the original question (not an error). Output re-passes the guard-in redactor. No temperature/top_p/top_k.

## Acceptance criteria
- [ ] Given empty history, when preparing a turn, then the aux LLM stub is called 0 times.
- [ ] Given history and the stub returning a rewritten query, when prepared, then retrieval receives the rewritten query.
- [ ] Given the aux call timing out, when prepared, then the original question is used and the turn continues.
- [ ] Given a rewritten query containing an email, then it is redacted before use (test).
