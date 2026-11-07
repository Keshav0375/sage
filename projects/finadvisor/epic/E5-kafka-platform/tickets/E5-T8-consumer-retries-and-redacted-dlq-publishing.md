---
key: "E5-T8"
title: "Consumer retries and redacted DLQ publishing"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T7"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.4", "deep-dive/04-components-and-responsibilities.md#4.7", "decision-logs.md#adr-013"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 85, "id": 6155670422, "url": "https://github.com/Keshav0375/FinAdvisor/issues/85"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Retry failing handlers, then publish the message to dlq.v1 with a redacted payload and a reason.

## Description
Extend the E5-T7 consumer: on handler failure retry with exponential backoff (settings KAFKA_CONSUMER_MAX_ATTEMPTS default 5 and KAFKA_RETRY_BACKOFF_MS default 500, added to deep-dive/06-interfaces-and-contracts.md#6.6 per R53), then publish to `dlq.v1` with the original key and the original envelope plus `{source_topic, consumer, error_code, reason, attempts}` (deep-dive/06-interfaces-and-contracts.md#6.4). The DLQ payload is redacted (D13j): the `payload` of the original envelope is replaced by a redacted form that keeps only id-like fields (keys ending `_id`, `sha256`, hash fields) and drops text fields; reason must not contain payload content. Undeserialisable (poison) messages go to the DLQ with the raw bytes dropped and `error_code=deserialisation_failed`; the offset is then committed so the partition does not stall. Envelope-check rejections from E5-T7 use this path. Add a DLQ envelope model to E5-T4's registry entry for `dlq.v1` if not yet present. Out of scope: operator re-publish tooling.

## Acceptance criteria
- [ ] Given a handler that always raises, when a message is consumed, then it is attempted KAFKA_CONSUMER_MAX_ATTEMPTS (5) times and exactly one record appears on dlq.v1 with attempts == that value and a non-empty reason (integration test).
- [ ] Given a poison message of invalid bytes, when consumed, then one dlq.v1 record exists with error_code `deserialisation_failed` and the consumer then processes the next valid message on the same partition.
- [ ] Given an event whose envelope tenant differs from its key, when consumed, then a dlq.v1 record exists with reason `envelope_key_mismatch` and the original key.
- [ ] Given a failed event whose payload contains a text field `redacted_question`, when the DLQ record is read, then that text is absent and the id fields are preserved (unit test on the redactor).
- [ ] Given a dlq.v1 record, when read, then it validates against the registered dlq.v1-value schema.
