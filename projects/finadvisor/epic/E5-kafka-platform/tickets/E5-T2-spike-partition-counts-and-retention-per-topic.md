---
key: "E5-T2"
title: "Spike: partition counts and retention per topic"
epic: "E5"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E0-T14"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.4", "decision-logs.md#adr-013", "decision-logs.md#adr-029"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 79, "id": 6155663578, "url": "https://github.com/Keshav0375/FinAdvisor/issues/79"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Decide partitions and retention for each topic within the 1,500-partition limit, including the delete-policy topics, and record them as an ADR.

## Description
Round 4 amendment (ADR-013 amended, ADR-029, R4-D6). Deep-dive/06-interfaces-and-contracts.md#6.4 says partition counts are 'set in E5 within those limits' (Confluent Basic: 1,500 partitions, 1,000 ACLs, 50 API keys). Topics: docs.bronze.v1, docs.silver.v1, chunks.contextualized.v1, chunks.indexed.v1, ingest.analytics.v1, acl.changes.v1, chat.audit.v1, chat.usage.v1, eval.sample.v1, eval.events.v1, dlq.v1 (11 topics; no `erasure.requested.v1`, because no erasure request travels on Kafka, ADR-029). Keys are tenant_id, about 1-5k events/day, tens of tenants.

Quote 6.4: 'subject-bearing topics are delete-policy with retention 7 d and `segment.ms` 1 d, payloads limited to ids and `pseudonym_id`'. The subject-bearing topics are acl.changes.v1, chat.audit.v1, chat.usage.v1, eval.sample.v1 and eval.events.v1: `cleanup.policy=delete`, `retention.ms` = 7 d, `segment.ms` = 1 d (about an 8 d window, because a record leaves only when its segment rolls and is then deleted). The other topics carry no subject data and keep a retention the spike sets; `dlq.v1` retention is at least the longest source topic (its payload is redacted).

Spike work: (1) in the Confluent console or via the API on a Basic cluster, confirm that `segment.ms` is editable (Confluent minimum 4 h) and whether any cap on `retention.ms` applies (UNVERIFIED; `max.compaction.lag.ms` minimum is 7 d on Basic, so the topics must not use compaction); (2) produce the table of partitions and `retention.ms` per topic with the arithmetic against 1,500 (include replication factor if the limit counts it); (3) state the API keys (4 service accounts) and ACLs used against 50 and 1,000; (4) note local compose values. Record as an ADR addendum under ADR-013. The values feed E5-T3 and E5-T13. Out of scope: creating topics.

## Acceptance criteria
- [ ] Given the ADR table, when partitions are summed over all 11 topics, then the total is <= 1,500 with at least 50% headroom, and the sum is shown.
- [ ] Given the five subject-bearing topics, when the ADR table is read, then each row states `cleanup.policy=delete`, `retention.ms` = 604800000 and `segment.ms` = 86400000, or states the Confluent Basic cap found by the spike and the resulting window in days.
- [ ] Given the spike, when finished, then the ADR records whether `segment.ms` is editable on Basic and its minimum, with the console or API output quoted; a topic using compaction fails the review check.
- [ ] Given the ADR, when read, then it states 4 service accounts and the ACL count against the 50-key and 1,000-ACL limits, and dlq.v1 retention >= the longest source topic.
