---
key: "E5-T12"
title: "Integration test: chat survives a Kafka outage"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T10", "E4-T21"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.4", "deep-dive/04-components-and-responsibilities.md#4.7", "decision-logs.md#adr-013", "plan.md#e5"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 89, "id": 6155675153, "url": "https://github.com/Keshav0375/FinAdvisor/issues/89"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Prove chat requests succeed with the broker stopped and audit rows are delivered once afterwards.

## Description
Epic 'done when': with the broker stopped, a chat request still succeeds and its audit outbox rows are published after the broker returns, with no loss and no duplicates in the sink. Add an integration test suite (CI job with a Kafka service container and Postgres, using docker compose services from E5-T3) that: starts the API without Kafka credentials (chat-api has none), stops the broker, issues authenticated chat requests (whose audit rows are written through the outbox insert helper owned by E4-T21), asserts HTTP 200 and outbox rows with published_at NULL, starts the broker, runs the relay, and consumes chat.audit.v1 through a test sink using the E5-T7 consumer (processed_events dedupe). Also covers G-48's premise: the audit path is outbox + Kafka, not Kong logs. Out of scope: the BigQuery sink.

## Acceptance criteria
- [ ] Given the broker is stopped, when 20 chat requests are sent, then all return 200 and 20 audit outbox rows exist with published_at NULL.
- [ ] Given the broker is restarted and the relay runs, when the sink is read, then it holds exactly 20 distinct event_ids (no loss) and 0 duplicates, and all outbox rows have published_at set.
- [ ] Given the relay is killed mid-batch and restarted, when the sink is read, then still 20 distinct event_ids (no duplicates after dedupe).
- [ ] Given the API environment, when its env vars are listed, then no KAFKA_* variable is set and requests still succeed (test asserts the absence).
