---
key: "E20-T2"
title: "Every backend and infra workflow emits ops events"
epic: "E20"
repo: "Sentinel"
size: "M"
status: "done"
depends_on: ["E20-T1"]
arch_refs: ["deep-dive/11-observability-and-ops-dashboard.md#11.3"]
issue: null
branch: "dev/backend-phase-10-ops-dashboard"
pr: "https://github.com/Keshav0375/Sentinel/pull/33"
updated: "2026-11-08"
---

## Summary
Add non-blocking `ops-event` calls to every state-changing step of the backend and infra workflows.

## Description
Source: backend task 10.2 (built in https://github.com/Keshav0375/Sentinel/pull/33).

Add non-blocking `ops-event` calls to every state-changing step of the backend and infra workflows; never from PR-triggered jobs (fork safety).

## Acceptance criteria
- [x] No PR-triggered job writes to the ledger
- [x] A failed ledger push does not fail the workflow

## Outcome
Merged in https://github.com/Keshav0375/Sentinel/pull/33 on 2026-10-28.
