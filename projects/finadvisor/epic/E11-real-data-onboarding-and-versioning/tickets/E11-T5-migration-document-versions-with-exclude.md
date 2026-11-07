---
key: "E11-T5"
title: "Migration: bitemporal document_versions with EXCLUDE"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T4", "E1-T5"]
arch_refs: ["deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.9", "decision-logs.md#adr-27", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Create document_versions with the valid-time EXCLUDE constraint and the idempotency index.

## Description
Alembic migration for `document_versions`, created here by E11. Enable `btree_gist` (available on Cloud SQL).

Arch (5.9): key `(tenant_id, version_id)`; `doc_id` (composite FK to `documents`), `version_key`, `valid_range daterange NOT NULL` (half-open, UTC days), `valid_from_basis` (`source` or `observed`), `system_range tstzrange NOT NULL DEFAULT tstzrange(clock_timestamp(), NULL)`, `bronze_sha256`, `bronze_uri`, `content_hash`, `parser_version`, `attribution_text`, `scan_passed`, `contract_passed`, `quarantine_reason`, `released_by`, `status` in (`ingesting`, `active`, `superseded`, `revoked`, `withdrawn`, `quarantined`, `known_pending`, `erased`), `created_at`. Unpartitioned. Exactly:

```sql
ALTER TABLE document_versions ADD CONSTRAINT document_versions_no_overlap
  EXCLUDE USING gist (tenant_id WITH =, doc_id WITH =, valid_range WITH &&)
  WHERE (upper_inf(system_range) AND status NOT IN ('ingesting', 'quarantined', 'erased'));
CREATE UNIQUE INDEX document_versions_idem ON document_versions
  (tenant_id, doc_id, version_key, bronze_sha256) WHERE upper_inf(system_range);
```

RLS and grants in the E1-T8 pattern; the indexer and `etl-public` roles write. Dates are UTC days; system time only via `clock_timestamp()`.

Out of scope: `reconcile_lineage` (E11-T9), the per-leaf EXCLUDE on `chunks` (partition-creation migration).

## Acceptance criteria
- [ ] Given two current rows of one document with overlapping `valid_range` and status `active` when the second is inserted then the EXCLUDE raises; the same overlap with status `quarantined` is allowed (test `test_no_overlap_constraint.py::test_overlap_rejected_for_active_only`).
- [ ] Given a row whose `system_range` is closed when a row with an overlapping `valid_range` is inserted then it succeeds, since only the current belief is constrained (test `test_historical_rows_unconstrained`).
- [ ] Given the same `(tenant, doc, version_key, bronze_sha256)` inserted twice with an open `system_range` then the unique index rejects the second (test `test_idempotency_index`).
- [ ] Given tenant A's row when tenant B's role queries then zero rows; `relforcerowsecurity` true (L0 leak matrix test).
