---
key: "E20-T1"
title: "Append-only ops ledger, ops-event action and frozen ops.v1 schema"
epic: "E20"
repo: "Sentinel"
size: "M"
status: "done"
depends_on: []
arch_refs: ["deep-dive/11-observability-and-ops-dashboard.md#11.3"]
issue: null
branch: "dev/backend-phase-10-ops-dashboard"
pr: "https://github.com/Keshav0375/Sentinel/pull/33"
updated: "2026-11-08"
---

## Summary
Orphan branch `ops-ledger` with one JSON file per event and deterministic `event_id`.

## Description
Source: backend task 10.1 (built in https://github.com/Keshav0375/Sentinel/pull/33).

Orphan branch `ops-ledger` with one JSON file per event and deterministic `event_id`; the `.github/actions/ops-event` composite action validates the envelope, enforces the per-kind allow-list and fails closed on secret-looking values; frozen `ops.v1` event and snapshot schemas with fixtures.

## Acceptance criteria
- [x] A replayed event is a no-op (same `event_id`)
- [x] Unknown fields are dropped and secret-looking values are refused
- [x] A ledger write failure warns and never fails the business job

## Outcome
Merged in https://github.com/Keshav0375/Sentinel/pull/33 on 2026-10-28.
