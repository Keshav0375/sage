---
key: "E21-T2"
title: "Azure Managed Redis B0, fail-closed backup and data-only restore"
epic: "E21"
repo: "Sentinel"
size: "M"
status: "done"
depends_on: ["E21-T1"]
arch_refs: ["deep-dive/05-data-and-memory.md#5.5", "deep-dive/12-evaluation.md#12.3"]
issue: null
branch: "dev/backend-phase-11-memory-hardening"
pr: "https://github.com/Keshav0375/Sentinel/pull/35"
updated: "2026-11-08"
---

## Summary
Terraform for Azure Managed Redis Balanced B0 (private endpoint, Entra auth, no access keys).

## Description
Source: backend task 11.2 (built in https://github.com/Keshav0375/Sentinel/pull/35).

Terraform for Azure Managed Redis Balanced B0 (private endpoint, Entra auth, no access keys). Pre-destroy `pg_dump` to the state storage account that fails closed unless `force_destroy_without_backup` is set. Data-only restore after apply when `incidents` is empty; restored `in_progress` rows are closed as `escalated`. `gha-deploy` scoped to its own database with a column-level UPDATE only.

## Acceptance criteria
- [x] Any Terraform, state or pg_dump error blocks the destroy
- [x] Restore skips `alembic_version`, `services`, `cache_entries` and `incident_checkpoints`
- [x] `gha-deploy` has no table-wide UPDATE and no server-wide data roles

## Outcome
Merged in https://github.com/Keshav0375/Sentinel/pull/35 on 2026-10-30.
