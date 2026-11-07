---
key: "E12-T12"
title: "GCS erasure step: bronze, silver and quarantine objects"
epic: "E12"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E12-T8", "E6-T4", "E6-T5"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.14", "decision-logs.md#adr-29", "decision-logs.md#adr-28"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Delete a document's GCS objects with soft delete 0 and check the bucket policy.

## Description
StoreStep `gcs`: resolve bronze (by sha256), silver Parquet and `quarantine/` objects for the document through `lineage_edges` (E11) and delete them; the data bucket has `soft_delete_policy` 0, versioning off and never a retention lock (5.14). Probe: list the prefixes, expect none; `window_closes_at` = now (immediate). A startup assertion reads the bucket metadata and fails the step with a clear error if soft delete is not 0 or versioning is on. The silver worker's own pre and post write tombstone check is in E6; this ticket adds the test that a Parquet written during an erasure is deleted. Out of scope: Terraform for the bucket (E10).

## Acceptance criteria
- [ ] Given a document with bronze, silver and quarantine objects, when the step runs, then listing each prefix returns zero objects and `rows_affected` equals the object count.
- [ ] Given a bucket with soft delete enabled, when the step starts, then it fails with `GCS_SOFT_DELETE_ENABLED` and does not delete.
- [ ] Given a silver write that lands after the tombstone, when the re-check runs, then the object is deleted and the ledger is the cause recorded (#1 object side).
- [ ] Given the same sha256 bronze object in firm B's prefix, then B's object remains (per-tenant bronze, #4).
