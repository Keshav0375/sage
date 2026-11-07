---
key: "E11-T12"
title: "Quarantine batch circuit, operator release and reject"
epic: "E11"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E11-T11"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.8", "deep-dive/04-2-source-lifecycle-and-cells.md#4.25", "decision-logs.md#adr-34", "decision-logs.md#adr-28"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 261, "id": 6263692711, "url": "https://github.com/Keshav0375/FinAdvisor/issues/261"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Pause a connector when over 5% of a batch is quarantined and record operator release or reject.

## Description
Add the batch circuit and the operator actions on quarantined versions.

Arch (6.8): more than 5% of a batch quarantined pauses the connector (`frozen_reason='contract_failure_rate'`, same column as E11-T8). Quarantine: operator `release` or `reject` is recorded (`released_by`, timestamp); compliance officers see a summary and never raw quarantined text (section 8.8). `release` of a version re-runs the gates (it does not bypass `contract_passed`/`scan_passed` in the indexer's check unless the operator release records both with a reason); `reject` keeps bytes under `quarantine/` and sets status per policy.

Interface: CLI/admin function `release_quarantined(version_id, operator, reason)` and `reject_quarantined(...)`; no new public HTTP endpoint unless the arch lists one (it does not; see Questions in epic.md).

Out of scope: the compliance summary view (E4/E8).

## Acceptance criteria
- [ ] Given a batch of 100 where 6 versions fail contract then the connector is frozen with reason `contract_failure_rate`; with 5 failures it is not (test `backend/tests/contracts/test_batch_circuit.py::test_over_five_percent_pauses`, PR).
- [ ] Given a quarantined version when an operator calls `release` then `released_by` and a timestamp are stored and the audit row exists; `reject` stores the same fields (test `test_release_and_reject_recorded`).
- [ ] Given the compliance summary query then it returns counts and reason codes and never the quarantined text (test `test_summary_never_returns_raw_text`).
