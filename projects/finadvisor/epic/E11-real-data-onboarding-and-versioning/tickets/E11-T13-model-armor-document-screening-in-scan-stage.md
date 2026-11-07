---
key: "E11-T13"
title: "Model Armor document screening in the scan stage"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T9", "E6-T5", "E11-T11", "E6-T20"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.25", "decision-logs.md#adr-36", "decision-logs.md#adr-34", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4 (#5)"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add Model Armor document screening to the E6 scan stage with the E4 client, failing closed.

## Description
Add step 3 of the ingest scan (4.25) to the silver scan stage, using the E4 Model Armor client (E4-T9) and the sanitiser and pattern steps already in E6.

Arch/plan: document windows under 65,536 tokens and 4 MB; at most 300 QPM of the shared 1,200 project quota (own throttle); `EXECUTION_SKIPPED` is treated as a failure and fails closed into quarantine; the screen runs behind the Model Armor feature flag with the ingest fallback (fail closed into quarantine, not skip). Any failure sets the version `status='quarantined'`, bytes under `quarantine/`, never silver. Latency is measured from the Cloud Run region before the timeout is fixed (E4-T1 spike result is the input).

Out of scope: the E4 client itself and the input screen; classifier ablation arms.

## Acceptance criteria
- [ ] Given a document of 70,000 tokens then it is split into windows each under 65,536 tokens and each is screened (test `backend/tests/scan/test_model_armor_windows.py::test_windowing_under_limit`).
- [ ] Given the stub returns `EXECUTION_SKIPPED` then the version is quarantined and a consumer continues with the next message (#5; test `test_execution_skipped_quarantines`, PR).
- [ ] Given the Model Armor feature flag is off or the client errors then ingest quarantines (fails closed) and nothing reaches silver (test `test_flag_off_fallback_fails_closed`).
- [ ] Given 400 documents in one minute then screening calls do not exceed 300 per minute (fake clock test `test_throttle_300_qpm`).
