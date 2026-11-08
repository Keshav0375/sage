---
key: "E11-T22"
title: "FCA kill switch and purge_source('fca_api')"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E11-T20", "E11-T5", "E12-T5", "E12-T6"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.20", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.11", "deep-dive/06-interfaces-and-contracts.md#6.9", "decision-logs.md#adr-26", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4 (#15, #30)"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 272, "id": 6263721134, "url": "https://github.com/Keshav0375/FinAdvisor/issues/272"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Suspend the FCA connector on 401 or 403 and purge the PUBLIC source with a pull-model row.

## Description
Implement the kill switch and `purge_source('fca_api')` (job `purge-source`) as the PUBLIC owner role `fa_etl_public`.

Arch (4.20): the connector auto-suspends on 401, 403 or a revocation notice (`frozen_reason`, shared with E11-T8). `purge_source` erases every FCA version, chunk, bronze and silver object found through `lineage_edges` (the PUBLIC deletion steps use the E12 delete helpers), writes a receipt, bumps `source_epoch` on the PUBLIC tenant row (making earlier cached answers unreachable via the cache key) and writes one row to the PUBLIC table `source_purges` (`purge_id`, `source_id`, `reason`, `requested_at`) in the SAME transaction. Pull model: no write on firm tenant tables, no cross-tenant role (ADR-002 D13a stands). The per-tenant execution by each `erasure-worker` is the E12 test of #15. FCA content never entered Kafka or BigQuery, so no step there. A quarterly drill runs the purge on fixtures and checks every store.

The `source_purges` table is created by E12-T6 (owner E12-T6); this ticket only writes to it.

## Acceptance criteria
- [ ] Given a 401 or 403 from the fixture server then the connector is suspended and `purge_source` is not run automatically (test `backend/tests/connectors/test_fca_kill_switch.py::test_401_403_suspend`).
- [ ] Given `purge_source('fca_api')` on fixtures then PUBLIC versions, chunks, bronze and silver objects for the source are zero, `source_epoch` is incremented and one `source_purges` row exists, all in one transaction (#15; test `test_purge_empties_public_and_bumps_epoch`, PR).
- [ ] Given a failure after the bump but before the `source_purges` insert then both are rolled back (test `test_epoch_and_purge_row_atomic`).
- [ ] Given the role `fa_etl_public` when it attempts any INSERT or DELETE on a firm tenant table then it is denied (L0 test `test_purge_role_has_no_firm_write`).
- [ ] Given a purge then re-ingest of the same FCA module is blocked until an explicit `release` is recorded on the tombstone ledger (#30; test `test_reingest_blocked_until_release`, PR, using the `erasure_ledger` created by E12-T5).
