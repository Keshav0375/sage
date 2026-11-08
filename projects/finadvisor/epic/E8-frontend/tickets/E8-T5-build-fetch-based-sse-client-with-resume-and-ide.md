---
key: "E8-T5"
title: "Build fetch-based SSE client with resume and idempotency"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T4", "E4-T27"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/06-interfaces-and-contracts.md#6.1", "deep-dive/04-components-and-responsibilities.md#4.4"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 202, "id": 6263592991, "url": "https://github.com/Keshav0375/FinAdvisor/issues/202"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
A typed SSE client posts a chat turn with an Idempotency-Key and resumes from Last-Event-ID after a drop.

## Description
Implements deep-dive/06-interfaces-and-contracts.md §6.2 and 6.1. src/lib/sse.ts, fetch + ReadableStream (not EventSource, because of the Authorization header and POST), parsing with eventsource-parser. Typed discriminated union for events turn, meta, tool, delta, citation, refusal, error, done with the 6.2 data shapes. `sendTurn({conversation_id?, message})`: generate `Idempotency-Key` (crypto.randomUUID) per user submit, POST /v1/chat, record `turn_id` from the `turn` event and the last `id:` seq. On a transport drop before `done`/`error`, reconnect to `GET /v1/chat/{turn_id}/events` with `Last-Event-ID: <last seq>`, bounded retries with backoff (config constants), ignoring events with seq <= last seen (no duplicate deltas). If the drop happens before the `turn` event, retry POST with the same key. `error` event with TURN_INTERRUPTED retryable: surface to caller, which resubmits with a NEW key. 409 IDEMPOTENCY_KEY_REUSED surfaces as an ApiError. Support AbortController. Ignore heartbeat comment lines. Out of scope: server side (E4).

## Acceptance criteria
- [ ] Given a stream cut after seq 3, when the client reconnects, then the GET carries `Last-Event-ID: 3` and the output has no duplicated delta text (vitest with a fake fetch).
- [ ] Given a drop before the `turn` event, when retried, then the POST reuses the same Idempotency-Key.
- [ ] Given an `error {TURN_INTERRUPTED, retryable:true}`, when received, then the client emits it to the caller and does not auto-resume; a resubmit uses a different key (unit test).
- [ ] Given a heartbeat comment line and a replayed event with seq <= last seen, when parsed, then neither reaches the caller.
- [ ] Given an unknown event name, when received, then it is ignored without throwing.
