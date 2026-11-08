---
key: "E12-T21"
title: "Canary drill at demo start"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T9", "E12-T10", "E12-T13", "E12-T14", "E12-T15", "E12-T16", "E10-T18"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.23", "decision-logs.md#adr-30", "deep-dive/09-observability.md#9.8"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 299, "id": 6263779638, "url": "https://github.com/Keshav0375/FinAdvisor/issues/299"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Drive a synthetic canary advisor through chat, a trace, events and BigQuery, erase it and record time to zero per observable store.

## Description
Implement `canary-drill` (a job run by `demo-up` right after the erasure job, E10-T18 calls it; compose runs the same drill minus provider windows). Steps: create a canary advisor with unique tokens; drive one chat turn (stub LLM and embeddings in compose) so a message, a Langfuse trace, outbox events, a Kafka message and a BigQuery row exist; issue the advisor erasure; poll each OBSERVABLE store (Postgres, index, cache, GCS, Langfuse, Kafka topic scan, BigQuery current rows) until zero and record seconds to zero per store in a `canary_runs` JSON object (GCS) and an OTel metric. Stores with multi-day windows (Kafka, BigQuery) are recorded at the first later demo start after their window closes. BigQuery fail-safe, Cloud SQL PITR and provider retention are NOT claimed. The published numbers are the maxima over recorded canaries. A store that does not reach zero inside its documented window is a FAILED canary: the drill reports the store and its age, raises the E9 alert metric `canary_failed` and triggers an `erasure-verify` re-sweep of that request (E12-T17). Out of scope: a weekly cron (not wanted), editing the promise text.

## Acceptance criteria
- [ ] Given the compose stack and stub providers, when the drill runs, then it creates the canary, erases it, and records a time-to-zero for Postgres, index, cache, GCS and the Kafka scan (each a number, not null) and the run object is written.
- [ ] Given the Langfuse stub in `ignore` mode, when the drill runs past the Langfuse window (fake clock), then the canary is marked FAILED with store `langfuse` and its age, `canary_failed` fires, and an `erasure-verify` re-sweep of the request is triggered (test `test_canary_fails_when_store_not_zero`); the store's time-to-zero is never recorded as 0.
- [ ] Given a canary from a previous start whose Kafka window has closed, then the next drill fills its Kafka and BigQuery fields.
- [ ] Given the drill output, then it contains no entry for BigQuery fail-safe, PITR or provider retention (those are absent, not zero).
- [ ] `demo-up` calls the drill after the erasure job and not before (script-order test).
