---
key: "E6-T7"
title: "silver worker role: consume bronze, emit silver, guard writes"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T6", "E5-T7", "E5-T9", "E5-T11", "E5-T15"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/04-1-key-flows.md#4.14", "deep-dive/04-2-source-lifecycle-and-cells.md#4.17", "decision-logs.md#adr-028", "decision-logs.md#adr-014"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 161, "id": 6263520802, "url": "https://github.com/Keshav0375/FinAdvisor/issues/161"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Wire the silver transform into an E5 worker consumer that reads docs.bronze.v1, checks the erasure ledger before and after writing, and emits docs.silver.v1.

## Description
Arch (4.7): role `silver` consumes `docs.bronze.v1`, writes silver Parquet and rejects, emits `docs.silver.v1`. Handler on the E5 consumer framework (envelope check, `processed_events` dedupe, retries, `dlq.v1`, `app.tenant_id` from the key). Order: read bronze bytes by `bronze_uri`; Docling parse; ingest scan hook (a no-op pass in this ticket; the sanitiser and pattern stage are E6-T20, Model Armor screening E11-T13); transform (E6-T5); validation and write (E6-T6); update `parser_version`; emit `docs.silver.v1` (ids and silver URI, no text). Register under `WORKER_ROLES=silver`.

Round 4 (ADR-028, 4.7, ADR-013 amended): this is a sink. 'It checks the tombstone before and after writing Parquet and deletes its own output if a tombstone appeared.' Before the write it calls the E5-T15 uncached helper for `(tenant_id, doc_key, sha256)` of the version; a hit drops the message with a counted reason `tombstoned` and writes nothing; if the ledger cannot be read the worker pauses (E5-T15 behaviour). After the Parquet write it calls the helper again; if a tombstone appeared in between it deletes the `silver/tenant_id=/doc_id=/version=/` prefix it just wrote and emits no `docs.silver.v1`. PUBLIC envelope or key mismatch goes to `dlq.v1` (framework; assert it). Out of scope: the framework (E5), the scan rules (E6-T20).

## Acceptance criteria
- [ ] Given a docs.bronze.v1 message, when consumed, then Parquet exists under the versioned prefix, `docs.silver.v1` is emitted once and `processed_events` has the event_id; the same message delivered twice emits one `docs.silver.v1`.
- [ ] Given a ledger tombstone for the document before the message, when consumed, then no Parquet object is written, no `docs.silver.v1` is emitted and the drop is counted `tombstoned` (test_silver_drops_tombstoned).
- [ ] Given a tombstone inserted after the Parquet write but before the second check (hook in the test), when consumed, then the version prefix is empty afterwards and no `docs.silver.v1` is emitted (test_silver_deletes_own_output).
- [ ] Given the ledger read raising, when consumed, then nothing is written, the offset is not committed and the partition is paused.
- [ ] Given an envelope whose tenant_id differs from the key, or a PUBLIC tenant message, when consumed, then it lands in `dlq.v1` and nothing is written.
