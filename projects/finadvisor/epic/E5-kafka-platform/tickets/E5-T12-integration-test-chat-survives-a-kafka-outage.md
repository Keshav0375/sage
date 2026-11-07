---
key: "E5-T12"
title: "Integration tests: chat and ACL survive a Kafka outage"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T10", "E5-T11", "E4-T21"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.4", "deep-dive/04-components-and-responsibilities.md#4.7", "decision-logs.md#adr-013", "decision-logs.md#adr-022", "plan.md#e5"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 89, "id": 6155675153, "url": "https://github.com/Keshav0375/FinAdvisor/issues/89"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Prove chat requests succeed with the broker stopped, audit rows are delivered once afterwards, and an ACL tightening is enforced within 60 s with Kafka down.

## Description
Epic 'done when': with the broker stopped, a chat request still succeeds and its audit outbox rows are published after the broker returns, with no loss and no duplicates in the sink. Add an integration suite (CI job with a Kafka service container and Postgres, compose services from E5-T3) that: starts the API without Kafka credentials, stops the broker, issues authenticated chat requests (audit rows are written through the outbox helper owned by E4-T21), asserts HTTP 200 and outbox rows with published_at NULL, starts the broker, runs the relay, and consumes chat.audit.v1 through a test sink on the E5-T7 consumer (processed_events dedupe).

Round 4 addition (ADR-022 amended, R4-D7): a second test stops the broker, a `tenant_admin` tightens a document's ACL (a pending `acl_change_requests` row), the E5-T11 applier polls, and a principal below the new tier asking for that content is refused within 60 s (retrieval returns no chunk; the refusal path of E4-T18). Out of scope: the BigQuery sink.

## Acceptance criteria
- [ ] Given the broker is stopped, when 20 chat requests are sent, then all return 200 and 20 audit outbox rows exist with published_at NULL.
- [ ] Given the broker is restarted and the relay runs, when the sink is read, then it holds exactly 20 distinct event_ids and 0 duplicates, and all outbox rows have published_at set; after killing the relay mid-batch and restarting, still 20.
- [ ] Given the broker is stopped and an ACL tightening request is pending, when the applier has polled, then a question from a principal below the new tier is refused (no chunk of that document in the result) within 60 s of the request (test_acl_tighten_with_kafka_down).
- [ ] Given the API environment, when its env vars are listed, then no KAFKA_* variable is set and requests still succeed (test asserts the absence).
