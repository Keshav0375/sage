---
key: "E5-T2"
title: "Spike: partition counts and retention per topic"
epic: "E5"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E0-T14"]
arch_refs: ["decision-logs.md#adr-013", "deep-dive/06-interfaces-and-contracts.md#6.4"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 79, "id": 6155663578, "url": "https://github.com/Keshav0375/FinAdvisor/issues/79"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Decide partitions and retention for each topic within the 1,500-partition limit and record them as an ADR.

## Description
deep-dive/06-interfaces-and-contracts.md#6.4 says partition counts and retention are 'set in E5 within those limits' (Confluent Basic: 1,500 partitions, 1,000 ACLs, 50 API keys). Topics: docs.bronze.v1, docs.silver.v1, chunks.contextualized.v1, chunks.indexed.v1, ingest.analytics.v1, acl.changes.v1, chat.audit.v1, chat.usage.v1, eval.sample.v1, eval.events.v1, dlq.v1. Keys are tenant_id (per-tenant ordering), ~1-5k events/day, tens of tenants (52 LIST partitions in Postgres). Produce a table of partitions and retention.ms per topic with the arithmetic against the 1,500 limit (include replication factor if the limit counts it, per Confluent docs), and note the local compose values. Record as an ADR. The values feed E5-T3 (local topic creation) and E5-T13 (Terraform). Out of scope: creating topics.

## Acceptance criteria
- [ ] Given the ADR table, when partitions are summed over all 11 topics, then the total is <= 1,500 with a stated headroom of at least 50%, and the sum is shown in the ADR.
- [ ] Given each topic row, when read, then it has a partitions value and a retention value with a one-line reason; dlq.v1 retention is at least as long as the longest source topic.
- [ ] Given the ADR, when read, then it states how many API keys (4 service accounts) and ACLs the design uses against the 50 and 1,000 limits.
