---
key: "E5-T6"
title: "Idempotent producer with traceparent and PUBLIC guard"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T5"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.4", "deep-dive/04-components-and-responsibilities.md#4.7", "decision-logs.md#adr-013"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 83, "id": 6155668231, "url": "https://github.com/Keshav0375/FinAdvisor/issues/83"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Provide a producer wrapper that serialises with Schema Registry, sets headers and the tenant key.

## Description
In `events/producer.py` wrap confluent-kafka 2.16.1 `Producer` with `enable.idempotence=true`, acks=all, JSON Schema serialisation via Schema Registry, key = tenant_id (utf-8), and the Kafka header `traceparent` taken from the envelope trace_context / current OTel span (deep-dive/06-interfaces-and-contracts.md#6.4). `produce(envelope)` validates the envelope against its E5-T4 model, resolves the topic from the registry, and returns after delivery callback (sync `flush` variant for the relay, because the relay must know delivery succeeded before marking published_at). Refuses envelopes whose `envelope.tenant_id` != key by construction (key is derived from tenant_id). Config from Settings: KAFKA_BOOTSTRAP, KAFKA_API_KEY, KAFKA_API_SECRET (SASL_SSL when a key is set, PLAINTEXT locally). chat-api must not import this module (import-linter contract; chat-api has no Kafka credentials). Out of scope: outbox reading, consumers.

## Acceptance criteria
- [ ] Given the local broker, when an envelope is produced, then the consumed record has key == tenant_id, a `traceparent` header equal to the producing span's context, and a value that deserialises against the registered schema (integration test).
- [ ] Given an envelope that fails its model validation, when produce is called, then it raises and nothing is written to the topic.
- [ ] Given the producer config, when inspected, then `enable.idempotence` is true and `acks` is `all` (unit test on built config).
- [ ] Given the import-linter configuration, when `lint-imports` runs, then a contract fails if the chat-api package imports `events.producer` (contract present and passing on main, failing in a test fixture that violates it).
