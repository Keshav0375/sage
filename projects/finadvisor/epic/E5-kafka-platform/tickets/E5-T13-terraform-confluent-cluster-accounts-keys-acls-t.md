---
key: "E5-T13"
title: "Terraform: Confluent cluster, accounts, keys, ACLs, topics"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T1", "E5-T2", "E5-T5"]
arch_refs: ["decision-logs.md#adr-013", "deep-dive/06-interfaces-and-contracts.md#6.4", "deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/11-tech-stack.md", "decision-logs.md#adr-029"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 90, "id": 6155676253, "url": "https://github.com/Keshav0375/FinAdvisor/issues/90"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Provision the Confluent Basic cluster, Schema Registry, topics with their retention policies, and per-service accounts, API keys and ACLs.

## Description
In terraform/ add a confluent module (provider version pinned per deep-dive/11-tech-stack.md). Create the Basic cluster in us-central1 FIRST (registry region follows, D13q) and Schema Registry Essentials; the 11 topics with partitions and retention from the E5-T2 ADR. Round 4 (ADR-013 amended, ADR-029): the subject-bearing topics (acl.changes.v1, chat.audit.v1, chat.usage.v1, eval.sample.v1, eval.events.v1) are created with `cleanup.policy=delete`, `retention.ms=604800000` and `segment.ms=86400000` as set by E5-T2 (or the cap that spike found); a plan check fails if any topic uses compaction. Four service accounts `fa-worker`, `etl`, `etl-public`, `eval`, each with its own Kafka API key and Schema Registry key, secrets in Secret Manager (no secret in state output). Kafka ACLs per account, least privilege from the catalogue: fa-worker produces/consumes silver, contextualizer, indexer, eval-judge, bq-sink and relay topics and groups `cg.*` and writes dlq.v1; the `acl-applier` needs NO Kafka ACL or group (it polls Postgres, E5-T11); `acl.changes.v1` is produced by the relay and consumed by `cg.bq-sink` only. etl produces docs.bronze.v1; etl-public produces ingest.analytics.v1 only; eval produces eval.events.v1. No ACL or key for chat-api. A smoke script registers the schemas (E5-T5) against the cloud registry. Within 50 keys, 1,000 ACLs, 1,500 partitions. Out of scope: Cloud Run wiring (E10).

## Acceptance criteria
- [ ] Given `terraform validate` and `plan` in CI, when run, then validate passes and the plan shows 4 service accounts, 4 distinct Kafka API keys, 11 topics and 0 resources for chat-api.
- [ ] Given the plan JSON, when the policy script runs, then it fails if two accounts share a key, any ACL uses `User:*`, any topic has cleanup.policy containing `compact`, or any of the five subject-bearing topics lacks retention.ms=604800000 and segment.ms=86400000; it passes on the real plan.
- [ ] Given the plan, when ACLs are listed, then no ACL grants a consumer group named like `cg.acl-applier` (test_no_acl_applier_group).
- [ ] Given the plan, when counted, then partitions <= 1,500, ACLs <= 1,000, API keys <= 50 (script prints the counts).
- [ ] Given the applied cluster, when the `etl-public` key produces to chat.audit.v1, then the broker returns TOPIC_AUTHORIZATION_FAILED, and `fa-worker` can produce there; the registration script then yields 11 subjects.
