---
key: "E4-T13"
title: "turn_events store and SSE v2 event encoding"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T4"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.2", "decision-logs.md#ADR-007"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 105, "id": 6155693225, "url": "https://github.com/Keshav0375/FinAdvisor/issues/105"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Persist ordered events per turn and encode them as SSE with ids and a client-safe schema.

## Description
Define event models (6.2): turn, meta, tool, delta, citation, refusal, error, done with exact data shapes; encode as 'id: <seq>\nevent: <name>\ndata: <json>'. Implement an EventSink that assigns strictly increasing seq per turn (turn at seq 0), inserts into turn_events (table from E1 schema; if absent see questions) in short transactions, batching delta events (documented interval) so the DB is not hit per token, and sends heartbeat comment lines every SSE_HEARTBEAT_S. Client-visible events are built only from these models: tool events carry tool name, status, tool_use_id; no payloads, inputs or exception text (G-04); error events carry {code, retryable} only. Do not make DB calls while holding a stream open longer than a short tx.

## Acceptance criteria
- [ ] Given events of every type are emitted in a test turn, when serialized, then none contains tool input/output payloads or exception text (test over all event types with a poisoned tool result and exception).
- [ ] Given a turn, when events are persisted, then seq is 0,1,2,... strictly increasing with no gaps and turn is seq 0.
- [ ] Given SSE_HEARTBEAT_S=1 and no events for 3 s, when streaming, then at least 2 comment lines ': hb' are sent.
- [ ] Delta batching: 1000 token deltas produce fewer than 1000 inserts (assert insert count).
