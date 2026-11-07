---
key: "E4-T21"
title: "Outbox writer and turn-persist transaction (no text events)"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T19", "E4-T20", "E1-T21", "E1-T23"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/06-interfaces-and-contracts.md#6.2", "deep-dive/06-interfaces-and-contracts.md#6.4", "decision-logs.md#adr-007", "decision-logs.md#adr-013"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Write chat.audit, chat.usage and sampled eval.sample outbox rows carrying ids, hashes, scores and flags only, in the turn-persist transaction.

## Description
Module events (04 §4.5): insert-only outbox writer taking the current transaction; no Kafka client or credentials in chat-api (import-linter contract + test). Turn persist = one short transaction: assistant message (retrieval_degraded, finish_reason, as_of, redacted citations and redacted answer text in Postgres `messages`), final turn_events flush, outbox rows chat.audit and chat.usage (tokens in/out, cache tokens, model used, latency) and, with probability EVAL_SAMPLE_RATE on completed turns, eval.sample.v1; answer_cache write (E3 store) when eligible (no side-effect tool, verifier passed, no escalation).

Round 4 (ADR-013 amended 2026-11-07, R4-D19 M5, test #15): quote 6.4 'chat.audit.v1 ... {ids, hashes, retrieved chunk ids, scores, flags (model, gate result, retrieval_degraded); no text}; eval.sample.v1 ... {message_id, chunk ids, hashes, flags; no text, the judge reads the redacted text from Postgres `messages` by `message_id`}'. The writer builds payloads from the E5-T4 models (no answer, question or excerpt text; the `FORBIDDEN_TEXT_FIELDS` list is enforced at write time and a violation raises, rolling back the transaction), subject-bearing payloads carry the advisor's `pseudonym_id` from the Principal (E1-T23), never `advisor_id`, and flags include `guard_degraded` (from E4-T9) and `as_of_source`. Out of scope: the relay and Kafka (E5), the judge (E7).

## Acceptance criteria
- [ ] Given a completed turn, when persisted, then one chat.audit and one chat.usage outbox row exist in the same transaction as the assistant message (kill-after-message test: no orphan rows).
- [ ] Given PII and an answer text in the stubbed turn, when outbox payloads are scanned, then none contains the question, answer or any citation excerpt text, and the row set contains no key in FORBIDDEN_TEXT_FIELDS, while `messages` holds the redacted answer (test_outbox_payloads_carry_no_text).
- [ ] Given a payload builder called with an `answer` field, when written, then it raises and no outbox row exists (negative control).
- [ ] Given EVAL_SAMPLE_RATE=1.0 an eval.sample row with message_id is written; at 0.0 none (seeded-RNG test); the subject payloads carry pseudonym_id and no advisor_id.
- [ ] Given chat-api code, importing a kafka client fails the import-linter contract.
