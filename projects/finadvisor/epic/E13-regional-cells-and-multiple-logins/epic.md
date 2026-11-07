---
key: "E13"
title: "Regional cells and multiple logins"
phase: 3
phase_name: "Real data and lifecycle"
repo: "FinAdvisor"
status: "todo"
depends_on: ["E1", "E2", "E4", "E5", "E6", "E12"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "deep-dive/04-2-source-lifecycle-and-cells.md#4.22", "deep-dive/06-interfaces-and-contracts.md#6.11", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.6", "deep-dive/08-security-and-privacy.md#8.2", "deep-dive/08-security-and-privacy.md#8.7", "decision-logs.md#adr-031", "decision-logs.md#adr-032", "decision-logs.md#adr-033", "decision-logs.md#adr-038", "decision-logs.md#adr-039"]
issue: null
updated: "2026-11-07"
---

## Goal
A firm's data lives only in its home cell, a wrong-cell request is refused without touching data, a tenant can move cell, and one person can work in several firms with one token per firm. Local two-cell docker compose only; no real second region (K-R4-1).

## Scope
- Signed static `cells.json` (E13-T1, T2, T3): schema, Ed25519 signature, GCS with baked fallback, 60 s refresh, no control-plane database, `GET /resolve?slug=`.
- Cell isolation (E13-T4, T6, T8, T9, T10): `principal` returns 421 plus hint with zero DB reads on mismatch; no cross-cell replication or failover; PUBLIC ingested per cell with a manifest and a drift alert (the cell-versus-cell pair of the E12 reconcile job).
- Two-cell compose suite and cell-down behaviour (E13-T6, T7); Cloud Run in one region only.
- Residency wording and global-data list in the privacy notice (E13-T12).
- Tenant move (E13-T13 to T16): `move-tenant` job, states `active`, `freezing`, `copying`, `verifying`, `cutover`, `draining`, `source_erased`; E13-T10 and E13-T16 need E12.
- Multiple logins (E13-T5, T11): project-level verify, `firebase.tenant` equals URL tenant and cell map, one token per firm, no identity merge; alias fallback if the E1 spike failed.

## ADRs
ADR-031 (cells), ADR-032 (multiple logins), ADR-033 (tenant move, entitlement), ADR-038 (residency wording), ADR-039 (validation amendments).

## Exit criteria
- Stopping `cell-eu` leaves US tenants passing, EU tenants get 503 `CELL_UNAVAILABLE`, no US data touched (#6). A provider outage returns `LLM_UNAVAILABLE` in every cell and is not a cell failure.
- A wrong-cell request returns 421 and the DB query log is empty (#16). A compose separation test shows a service in one cell cannot resolve the other. PUBLIC manifests equal across cells; a deliberate difference raises the drift alert.
- `cells.json` unreadable: last good copy, then the baked fallback; a tampered signature is rejected.
- Token A on firm B's resource gives 403 or 421 (#17, server side; the browser part is in E8).
- Killing the move target mid-copy leaves the source intact and unfrozen and the target empty; success path counts and hashes equal (#18). Erase of the moved source issues a receipt after the 7-day grace (shortened in test).
- Residency wording and global-data list appear in the privacy notice; private ingest stays gated by `llm_egress_ack` (tested in E11).
