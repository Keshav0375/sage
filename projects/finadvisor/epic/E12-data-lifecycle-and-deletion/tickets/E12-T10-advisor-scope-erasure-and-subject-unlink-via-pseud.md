---
key: "E12-T10"
title: "Advisor-scope erasure and subject unlink via pseudonym_map"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T8", "E4-T23", "E1-T23"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.12", "decision-logs.md#adr-29", "deep-dive/06-interfaces-and-contracts.md#6.9"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 287, "id": 6263754352, "url": "https://github.com/Keshav0375/FinAdvisor/issues/287"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Erase an advisor's conversations and events and unlink slow-store rows by deleting the pseudonym mapping first.

## Description
Scope `advisor` (`subject_ref` = `pseudonym_id`). Step 1, in the first transaction: tombstone `subject:<salted hash>` with an empty sha256 (E12-T8) and DELETE the `pseudonym_map` row, so surviving BigQuery, Kafka, Langfuse and log rows are unlinkable at once (unlinking is NOT reported as erasure, 4.19). Step 2: delete in this order `messages`, `turn_events`, `feedback`, `escalations`, `conversations`, `eval_scores`, then the `advisors` row, honouring `retention_class` for legal hold (escalations may be retained with the legal basis in the receipt); then VACUUM. Collect the advisor's `messages.trace_id` and BigQuery event ids BEFORE deleting `messages`, and persist them on the `erasure_steps` rows for the Langfuse and BigQuery steps (the scope resolver, lineage). Out of scope: the BigQuery, Langfuse, Kafka implementations.

## Acceptance criteria
- [ ] Given an advisor with 5 conversations, 40 messages and a pseudonym, when the request runs, then every listed table has 0 rows for that advisor and the `pseudonym_map` row is gone before the messages are deleted (ordering asserted by timestamps).
- [ ] Given the mapping is deleted, when a join from a surviving BigQuery-fixture row's `pseudonym_id` to an advisor is attempted, then it finds no advisor (unlink test).
- [ ] Given an escalation with `retention_class`, when the request runs, then it is retained and listed in the receipt `retained` array with its legal basis.
- [ ] Given a second advisor in the same tenant, then none of their rows change.
- [ ] The step persists trace ids and event ids before the messages are deleted: kill the process right after the delete and a re-run still has the ids (crash test).
