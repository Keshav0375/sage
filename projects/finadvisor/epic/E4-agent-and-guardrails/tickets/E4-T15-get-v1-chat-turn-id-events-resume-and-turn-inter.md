---
key: "E4-T15"
title: "GET /v1/chat/{turn_id}/events resume and TURN_INTERRUPTED"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T13", "E4-T14"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1", "deep-dive/06-interfaces-and-contracts.md#6.2"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 107, "id": 6155695586, "url": "https://github.com/Keshav0375/FinAdvisor/issues/107"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Resume a dropped stream from Last-Event-ID, tail to done, and detect dead producers.

## Description
Endpoint (6.1/6.2): owner of the turn only (403/404 otherwise, RLS-scoped); header Last-Event-ID; replay turn_events with seq > Last-Event-ID, then tail (poll or LISTEN, documented) until done; heartbeat as in E4-T13. If the last persisted event is older than TURN_LEASE_S and no done/error exists, append once error {code: TURN_INTERRUPTED, retryable: true} and end; the append must be idempotent across concurrent resumers. Events older than SSE_REPLAY_TTL_S are no longer replayable (410 or documented code).

## Acceptance criteria
- [ ] Given a turn of 20 events and a client that disconnects after seq 7, when it reconnects with Last-Event-ID 7, then it receives exactly seq 8..N with no duplicates or gaps (test).
- [ ] Given the producer stops and TURN_LEASE_S passes, when two resumers connect concurrently, then exactly one TURN_INTERRUPTED error row exists in turn_events.
- [ ] Given another advisor's turn_id, when requested, then no events are returned (403/404 test).
- [ ] Given Last-Event-ID absent, the stream starts from seq 0.
