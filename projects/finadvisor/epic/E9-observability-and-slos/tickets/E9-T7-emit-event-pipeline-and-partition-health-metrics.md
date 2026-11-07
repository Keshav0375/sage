---
key: "E9-T7"
title: "Emit event-pipeline and partition health metrics"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T5", "E5-T8", "E5-T9", "E1-T12"]
arch_refs: ["deep-dive/09-observability.md#9.2", "deep-dive/09-observability.md#9.5"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 227, "id": 6263630799, "url": "https://github.com/Keshav0375/FinAdvisor/issues/227"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
outbox_oldest_age_s, consumer_lag, dlq_messages_total and default_partition_rows are emitted on a schedule.

## Description
Implements the 9.2 rows for outbox_oldest_age_s, consumer_lag{group}, dlq_messages_total and default_partition_rows ("rows in the DEFAULT chunks / messages partitions (bug signal)"). acl_apply_lag_s is E5's.
Using metrics.record (E9-T5):
- Worker background task (every 30 s, in roles outbox-relay and the consumer roles): outbox_oldest_age_s = now - min(created_at) of unpublished outbox rows (0 if none), read through the worker's tenant-safe path; consumer_lag{group} = end offset minus committed offset summed over the group's partitions; dlq_messages_total incremented in the E5-T8 DLQ publisher.
- default_partition_rows: count rows in chunks_default and messages_default (names as created by E1 migrations; check the schema) recorded as a gauge, emitted from the maintenance job (E1-T12) after its checks, with the job still exiting non-zero as E1-T12 defines.
Out of scope: alerting (E9-T15), the maintenance job's exit code.
The maintenance job runs every 15 min in demo mode (E10 schedules it, R76), so default_partition_rows is refreshed at that cadence.

## Acceptance criteria
- [ ] Given an unpublished outbox row created 90 s ago in a test DB, When the sampler runs, Then outbox_oldest_age_s is between 90 and 95; with no unpublished rows it is 0 (pytest test_pipeline_metrics.py, integration with Postgres).
- [ ] Given a consumer group committed at offset 10 with end offset 25 on one partition in the local Kafka, When sampled, Then consumer_lag{group}=15.
- [ ] Given a message that exhausts retries, When published to dlq.v1, Then dlq_messages_total increments by 1.
- [ ] Given one row inserted into the DEFAULT messages partition, When the maintenance job runs, Then default_partition_rows=1 is recorded and the job exits non-zero; with none it records 0 and exits zero.
