---
key: "E4-T21"
title: "Outbox writer and turn persist transaction"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T19", "E4-T20", "E1-T21"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.2", "decision-logs.md#ADR-007"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Write chat.audit, chat.usage and sampled eval.sample outbox rows in the turn-persist transaction.

## Description
Module events (4.5): insert-only outbox writer taking the current transaction; no Kafka client or credentials in chat-api (import-linter contract + test). Turn persist = one short transaction: assistant message (retrieval_degraded, finish_reason, redacted citations), final turn_events flush, outbox rows chat.audit and chat.usage (tokens in/out, cache tokens, model used, latency, tenant) and, with probability EVAL_SAMPLE_RATE on completed turns, eval.sample.v1; answer_cache write (E3 store) when eligible (no side-effect tool, verifier passed). Payloads use redacted text only. Event schema names/versions follow the 6.4 topic catalogue (verify against it).

## Acceptance criteria
- [ ] Given a completed turn, when persisted, then one chat.audit and one chat.usage outbox row exist in the same transaction as the assistant message (kill-after-message test: no orphan rows).
- [ ] Given EVAL_SAMPLE_RATE=1.0 an eval.sample row is written; at 0.0 none (seeded-RNG test).
- [ ] Given chat-api code, importing a kafka client fails the import-linter contract.
- [ ] Given PII in the stubbed answer, outbox payloads contain only redacted text (test).
