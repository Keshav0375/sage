---
key: "E6-T7"
title: "silver worker role: consume bronze, emit silver"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T6", "E5-T7", "E5-T9", "E5-T11"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/04-1-key-flows.md#4.14"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Wire the silver transform into an E5 worker consumer that reads docs.bronze.v1 and emits docs.silver.v1.

## Description
Arch (4.7): role `silver` consumes `docs.bronze.v1`, writes silver Parquet and rejects, emits `docs.silver.v1`. Implement the handler on the E5 consumer framework (envelope check, `processed_events` dedupe in the sink transaction, retries, then `dlq.v1`, `app.tenant_id` set from the event key). Handler: read bronze bytes from GCS by `bronze_uri`, run E6-T5 transform and E6-T6 validation, update `documents.parser_version`, produce `docs.silver.v1` (ids and silver URI, no text). Register under `WORKER_ROLES=silver`. Per 4.7, an envelope with a PUBLIC tenant or key mismatch goes to `dlq.v1` (framework behaviour; assert it). Out of scope: framework itself (E5).

## Acceptance criteria
- [ ] Given a docs.bronze.v1 message, when consumed, then Parquet exists, `docs.silver.v1` is emitted once and `processed_events` has the event_id (integration)
- [ ] Given the same message delivered twice, when consumed, then only one `docs.silver.v1` is emitted (test)
- [ ] Given an envelope whose tenant_id differs from the key, when consumed, then it lands in `dlq.v1` with a reason and nothing is written (test)
- [ ] Given a message for the PUBLIC tenant, when consumed by the silver role, then it goes to `dlq.v1` (test)
