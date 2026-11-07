---
key: "E9-T10"
title: "End-to-end trace test across Kong, API, DB and LLM"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T3", "E9-T4", "E2-T15"]
arch_refs: ["deep-dive/09-observability.md#9.1", "ADR-018"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
A compose test proves one trace spans Kong, chat-api, a DB query and an LLM call, and a Kafka consumer links to its producer.

## Description
Implements the Done-when item: "A single trace spans Kong, chat-api, a DB query and an LLM call, and a Kafka event's consumer span links to its producer span."
Add an integration test run against docker compose with Kong (opentelemetry plugin from E2-T15), chat-api, Postgres, Kafka, a worker, an OpenTelemetry Collector with a file or debug exporter writing spans as JSON, and a stubbed Anthropic/Voyage endpoint. The test sends POST /v1/chat, then reads collector output and asserts the span tree. Add the collector service and config to the compose file and set OTEL_EXPORTER_OTLP_ENDPOINT for services. Document how to run it in docs/runbooks/observability.md.
Out of scope: Cloud Trace itself (verified manually in the E9-T17 drill note).

## Acceptance criteria
- [ ] Given the compose stack up, When POST /v1/chat is sent through Kong, Then collector output holds one trace_id containing a Kong span, chat.turn, a DB span (asyncpg) and llm.stream with a child HTTP client span (pytest -m e2e test_e2e_trace.py).
- [ ] Given a turn that writes an outbox row, When the relay publishes and the worker consumes, Then a consumer.<role> span exists whose link's trace_id equals the turn's trace_id.
- [ ] Given the Kong plugin disabled, When the test runs, Then it fails on the missing Kong span (negative check documented in the test).
- [ ] Given the e2e run, When the span dump is scanned, Then no span attribute contains the request message text.
