---
key: "E4-T14"
title: "POST /v1/chat with Idempotency-Key and replay"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T13", "E1-T21"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1", "deep-dive/06-interfaces-and-contracts.md#6.2", "decision-logs.md#ADR-007"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 106, "id": 6155694411, "url": "https://github.com/Keshav0375/FinAdvisor/issues/106"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Idempotent chat endpoint: same key and body replays, different body returns 409.

## Description
POST /v1/chat requires header Idempotency-Key and body {conversation_id?, message}. turn_id derived from the Idempotency-Key (deterministic, per principal/tenant namespace). Short tx: insert turn_events seq 0 ON CONFLICT DO NOTHING plus store a request-body hash with the turn; if the row existed with the same hash, stream a replay of persisted events (then tail until done) instead of generating; a different hash returns 409 IDEMPOTENCY_KEY_REUSED. Missing header -> 400 with a stable code. Auth and principal first. Streams text/event-stream; Kong passes it unbuffered. Orchestrator call is a stub interface here (implemented in the orchestrator tickets).

## Acceptance criteria
- [ ] Given the same Idempotency-Key and body sent twice, when the second arrives, then the LLM stub is called once and the second response replays identical events (test counting stub calls).
- [ ] Given the same key with a different body, when posted, then status is 409 with code IDEMPOTENCY_KEY_REUSED.
- [ ] Given two concurrent requests with the same key, when both arrive, then exactly one generation runs (race test).
- [ ] Given a different tenant using the same key string, when posted, then it is a distinct turn (no cross-tenant replay).
