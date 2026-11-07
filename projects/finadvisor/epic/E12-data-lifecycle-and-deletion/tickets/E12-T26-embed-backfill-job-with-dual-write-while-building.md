---
key: "E12-T26"
title: "embed-backfill job with dual write while building"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T25", "E12-T4", "E6-T10"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.27", "decision-logs.md#adr-35", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.10", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#20"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Embed every distinct chunk text with the new model under a 25% RPM cap and write both generations during the build.

## Description
Job `embed-backfill --model M`: sets the generation `building`, copies parents, then for every distinct chunk content (reuse via the `(tenant_id, chunk_hash, embed_model)` index) embeds with the new model through the Voyage client under a semaphore of `EMBED_BACKFILL_RATE_FRACTION` (0.25) x RPM (batch API if E12-T4 recommends it), and inserts green child rows in resumable batches (checkpoint per tenant and document). While `building`, the E6-T10 indexer writes both generations for new and changed documents. Erasure and withdrawal delete by `doc_id` and therefore hit both generations (E12-T9). Out of scope: validation, flip, retire.

## Acceptance criteria
- [ ] Given 500 chunks and a fake Voyage client, when the backfill runs, then green has 500 child rows with the new `embed_model` and the request rate never exceeds 0.25 x RPM in any 60 s window.
- [ ] Given the job killed halfway, when it restarts, then it resumes from the checkpoint and ends with the same row count and no duplicates (unique identity key).
- [ ] Given the indexer publishes a new document while `building`, then chunks exist in both generations for it.
- [ ] Given a document erased during the backfill, when both finish, then it has zero rows in both generations and a receipt exists (#20).
