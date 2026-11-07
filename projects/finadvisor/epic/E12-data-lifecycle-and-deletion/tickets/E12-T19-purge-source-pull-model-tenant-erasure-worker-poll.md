---
key: "E12-T19"
title: "purge_source pull model: tenant erasure-worker polls source_purges"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T6", "E12-T7", "E12-T9", "E11-T22"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.20", "decision-logs.md#adr-26", "decision-logs.md#adr-29", "decision-logs.md#adr-39", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#15", "deep-dive/06-interfaces-and-contracts.md#6.9"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Each firm tenant's erasure-worker enqueues its own source request from a PUBLIC purge row and erases quoted FCA text.

## Description
The command and the PUBLIC-side purge (bump `source_epoch`, write `source_purges`, suspend the connector) are E11; this ticket owns the pull. In every erasure-worker run, under THAT tenant's `fa_worker` role, SELECT `source_purges` rows not yet handled and INSERT its own `deletion_requests` row (scope `source`, source `fca_api`, `subject_ref` = `purge_id`), idempotent on `(tenant_id, purge_id)` (unique index of E12-T5; use ON CONFLICT DO NOTHING). Then execute it like any request: delete the messages and cached answers that quote FCA text (found via `retrieval_chunk_ids` and `source_document_ids` against the purged documents), with the usual steps and receipt. There is no cross-tenant write and no cross-tenant role (ADR-002 D13a, ADR-039). FCA content never entered Kafka or BigQuery, so those stores need no step. A stopped tenant catches up at its next run (`demo-up` runs the erasure job first). Out of scope: PUBLIC erasure, the drill schedule (quarterly, ops).

## Acceptance criteria
- [ ] Given fixtures with 2 firm tenants and a `source_purges` row, when each tenant's worker runs once, then each has exactly one `deletion_requests` row for that `purge_id`, and re-running adds no row (#15; idempotency).
- [ ] Given messages and cached answers quoting FCA text in firm A, when the request executes, then they are gone and a receipt is issued; messages not citing FCA are untouched (#15).
- [ ] Given the L0 leak matrix, then `fa_etl_public` has no INSERT on any firm `deletion_requests` and no cross-tenant role exists (grants test).
- [ ] Given a tenant worker that was stopped during the purge, when it starts later, then it enqueues and executes the pending purge (catch-up test).
- [ ] Given the Kafka and BigQuery fixtures, then they contain no FCA text or chat answer text after the purge (absence scan, #15).
