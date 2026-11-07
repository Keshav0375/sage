---
key: "E7-T16"
title: "Emit eval.sample.v1 outbox rows and thumbs feedback events"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T27", "E6-T19"]
arch_refs: ["deep-dive/04-1-key-flows.md#4.14", "deep-dive/06-interfaces-and-contracts.md#6.4", "deep-dive/09-observability.md#9.6", "ADR-017"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Have chat-api sample EVAL_SAMPLE_RATE of completed turns into the outbox and send feedback to eval.events.v1.

## Description
In chat-api's end-of-turn transaction (arch flow 1: "persist assistant message, turn_events, outbox rows (chat.audit, chat.usage, sampled eval.sample)") add the sampled `TurnSampled` outbox row {message_id, redacted question, redacted answer, cited excerpts (redacted)} for a fraction `EVAL_SAMPLE_RATE` (default 0.05, allowed 0.05-0.10, validated). Sampling is deterministic from message_id hash so tests are repeatable. Ensure `POST /v1/messages/{id}/feedback` (`{score: -1|1, comment?}`) writes `feedback` and an outbox `FeedbackRecorded` for `eval.events.v1`. Only redacted text enters the payload. Do this only if E4/E6 have not already implemented the pieces: check the repo and implement the missing parts. Out of scope: the relay (E5).

## Acceptance criteria
- [ ] Unit test: with EVAL_SAMPLE_RATE=0.10 over 1000 synthetic message ids between 8% and 12% are sampled; with 0 none; the setting rejects 0.5.
- [ ] Integration test: a completed turn selected by the sampler leaves one outbox row of type TurnSampled whose payload contains no raw PII fixture value.
- [ ] Integration test: POST feedback with score 1 creates a feedback row and a FeedbackRecorded outbox row; score 2 returns 422.
