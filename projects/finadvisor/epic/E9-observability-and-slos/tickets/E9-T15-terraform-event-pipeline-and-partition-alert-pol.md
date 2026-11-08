---
key: "E9-T15"
title: "Terraform: event pipeline and partition alert policies"
epic: "E9"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E9-T11", "E9-T7"]
arch_refs: ["deep-dive/09-observability.md#9.5", "deep-dive/09-observability.md#9.2"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 213, "id": 6263608226, "url": "https://github.com/Keshav0375/FinAdvisor/issues/213"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Alert policies exist for outbox age, ACL applier lag, consumer lag, DLQ non-empty and non-empty DEFAULT partitions.

## Description
Implements from deep-dive/09-observability.md §9.5: "outbox oldest age, ACL applier lag, consumer lag, DLQ non-empty, DEFAULT partition non-empty". Add terraform/alerts_events.tf using the E9-T11 channel. Thresholds fixed by resolution R72, overridable in tfvars:
- outbox_age: outbox_oldest_age_s > 300 for 5 min.
- acl_lag: acl_apply_lag_s > 120 (the principal cache TTL is 60 s, 6.1) for 5 min.
- consumer_lag: consumer_lag{group} > 1000 for 10 min.
- dlq_non_empty: increase of dlq_messages_total > 0 over 5 min.
- default_partition_non_empty: default_partition_rows > 0 over a 30 min window (the maintenance job runs every 15 min in demo, R76) (E1-T12 only makes the maintenance job exit non-zero; this is the alert).

## Acceptance criteria
- [ ] Given terraform plan, Then five policies exist with the names above (scripts/check_monitoring_tf.py assertion).
- [ ] Given the policy for default_partition_non_empty, When parsed, Then the condition metric is default_partition_rows with threshold 0 and comparison GT. Duration/alignment window is 1800 s.
- [ ] Given the E9-T17 drill inserts one row into a DEFAULT messages partition and runs the maintenance job in a scratch project, Then the incident opens within 45 minutes (30 min window plus one 15 min job run).
- [ ] Given the drill stops the acl-applier worker and POSTs an ACL change, Then acl_lag opens within 10 minutes.
