---
key: "E9-T4"
title: "Link consumer spans to producer spans over Kafka headers"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T2", "E5-T6", "E5-T7", "E5-T10"]
arch_refs: ["deep-dive/09-observability.md#9.1", "ADR-018"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
outbox.relay and consumer.<role> spans are emitted and each consumer span carries a span link to the producing span from the traceparent header.

## Description
Implements deep-dive/09-observability.md §9.1: "workers (traceparent carried in Kafka headers)", spans outbox.relay and consumer.<role>. The producer wrapper already sets traceparent (E5-T6) and the consumer base class exists (E5-T7).
Build: in the outbox-relay role (E5-T10) wrap each publish in an outbox.relay span, writing the current context into the Kafka traceparent header (via the E5-T6 wrapper, do not duplicate it). In the consumer base (E5-T7) start consumer.<role> for each message with a Link to the SpanContext extracted from traceparent (a link, not a parent, so batch/retry does not stretch traces); retries and DLQ publishing (E5-T8) stay inside the span. Attributes: topic, partition, offset, tenant_id, role, outcome. No payloads.
Out of scope: producer header logic, consumer semantics.

## Acceptance criteria
- [ ] Given a message produced inside a span S through the E5-T6 wrapper and consumed by the E5-T7 base in a test with an in-memory exporter, When the handler finishes, Then a span named 'consumer.<role>' exists whose links contain S's trace_id and span_id (pytest test_consumer_links.py).
- [ ] Given a message without a traceparent header, When consumed, Then consumer.<role> is still emitted with no links and no exception.
- [ ] Given a handler that raises, When retried then sent to the DLQ, Then the span has outcome='dlq' and error_code set, and its attributes contain no payload text.
- [ ] Given the outbox-relay role publishes 3 rows, When collected, Then three outbox.relay spans exist, each with topic and tenant_id attributes.
