---
key: "E5-T13"
title: "Terraform: Confluent cluster, accounts, keys, ACLs, topics"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E5-T1", "E5-T2", "E5-T5"]
arch_refs: ["decision-logs.md#adr-013", "deep-dive/06-interfaces-and-contracts.md#6.4", "deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/11-tech-stack.md"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 90, "id": 6155676253, "url": "https://github.com/Keshav0375/FinAdvisor/issues/90"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Provision the Confluent Basic cluster, Schema Registry, topics, and per-service accounts, API keys and ACLs.

## Description
In terraform/ add a confluent module (Confluent provider; pin version at implementation per deep-dive/11-tech-stack.md). Create: the Basic cluster in us-central1 FIRST (registry region follows, D13q) and Schema Registry Essentials; the 11 topics with the partitions and retention from the E5-T2 ADR; four service accounts `fa-worker`, `etl`, `etl-public`, `eval` each with its own Kafka API key and a Schema Registry API key, secrets written to Secret Manager entries (no secret in state output); Kafka ACLs per service account, least privilege from the catalogue: fa-worker produces/consumes silver, contextualizer, indexer, acl-applier, eval-judge, bq-sink and relay topics and consumer groups `cg.*`, and writes dlq.v1; etl produces docs.bronze.v1; etl-public produces ingest.analytics.v1 only; eval produces eval.events.v1. No ACL or key for chat-api. Provide a smoke script that registers the schemas (E5-T5) against the cloud registry. Counts must stay within 50 keys, 1,000 ACLs, 1,500 partitions. Out of scope: Cloud Run wiring (E10).

## Acceptance criteria
- [ ] Given `terraform validate` and `terraform plan` on the module, when run in CI, then validate passes and the plan shows 4 service accounts, 4 distinct Kafka API keys, 11 topics and 0 resources for chat-api.
- [ ] Given the plan, when a policy check script (conftest or a python test over `terraform show -json`) runs, then it fails if two service accounts share one API key or if any ACL uses principal `User:*`, and passes on the real plan.
- [ ] Given the plan, when counted, then partitions <= 1,500, ACLs <= 1,000, API keys <= 50 (script asserts and prints the counts).
- [ ] Given the applied cluster, when the `etl-public` key tries to produce to chat.audit.v1, then the broker returns TOPIC_AUTHORIZATION_FAILED (smoke test), and `fa-worker` can produce to chat.audit.v1.
- [ ] Given the applied cluster, when the schema registration script runs with the cloud registry, then 11 subjects exist.
