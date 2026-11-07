---
key: "E5-T6"
title: "Idempotent producer with traceparent and PUBLIC/FCA guard"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T5"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.4", "deep-dive/04-components-and-responsibilities.md#4.7", "decision-logs.md#adr-013", "decision-logs.md#adr-026"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 83, "id": 6155668231, "url": "https://github.com/Keshav0375/FinAdvisor/issues/83"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Provide a producer wrapper that serialises with Schema Registry, sets headers and the tenant key, and refuses fca_api content.

## Description
In `events/producer.py` wrap confluent-kafka 2.16.1 `Producer` with `enable.idempotence=true`, acks=all, JSON Schema serialisation via Schema Registry, key = tenant_id (utf-8), and the Kafka header `traceparent` from the envelope trace_context or current OTel span (6.4). `produce(envelope)` validates the envelope against its E5-T4 model, resolves the topic from the registry and returns after the delivery callback (a sync `flush` variant for the relay, which must know delivery succeeded before setting published_at). The key is derived from tenant_id, so envelope tenant != key cannot happen. Config: KAFKA_BOOTSTRAP, KAFKA_API_KEY, KAFKA_API_SECRET (SASL_SSL when a key is set, PLAINTEXT locally). chat-api must not import this module (import-linter contract).

Round 4 (ADR-013 amended, ADR-026, test #15): quote 6.4 'FCA Handbook API content never enters Kafka or BigQuery'. The producer rejects any envelope whose payload has `source == 'fca_api'` (or whose `licence_class` is the FCA class) on every topic, raising `FcaContentRejected` and writing nothing. Out of scope: outbox reading, consumers, the sink-side check (E5-T14).

## Acceptance criteria
- [ ] Given the local broker, when an envelope is produced, then the consumed record has key == tenant_id, a `traceparent` header equal to the producing span's context, and a value that deserialises against the registered schema (integration test).
- [ ] Given an envelope that fails its model validation, when produce is called, then it raises and nothing is written to the topic.
- [ ] Given an envelope whose payload has `source='fca_api'`, when produce is called on each pipeline and analytics topic, then `FcaContentRejected` is raised and the topic offset is unchanged (test_producer_rejects_fca_source, parametrised over topics).
- [ ] Given the producer config, when inspected, then `enable.idempotence` is true and `acks` is `all` (unit test).
- [ ] Given the import-linter configuration, when `lint-imports` runs, then a contract fails if the chat-api package imports `events.producer` (passing on main, failing on a violating fixture).
