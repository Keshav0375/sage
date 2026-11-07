---
key: "E12-T1"
title: "Spike: Cloud SQL backup expiry while the instance is stopped"
epic: "E12"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: []
arch_refs: ["deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.14", "decision-logs.md#adr-29", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#31"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 286, "id": 6263748616, "url": "https://github.com/Keshav0375/FinAdvisor/issues/286"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Measure on a non-prod instance whether automated backups expire on schedule while Cloud SQL is stopped, and record the result.

## Description
ADR-029 (amended 2026-11-07, R4-D18 V5) and deep-dive/05-1 5.14: automated backup retention is 7 d and PITR log retention is 7 d, but 'whether old backups expire while the instance is stopped is UNVERIFIED and is an E12 spike'. This result gates the 'backups within 7 d plus ledger replay' promise. On a throwaway non-prod Cloud SQL Enterprise instance set retention to the minimum the console allows (record the value), take an automated backup, stop the instance (activation policy NEVER) for longer than the retention, then list backups with `gcloud sql backups list` before start, right after start and 24 h after start. Write the finding to `docs/adr/cloud-sql-backup-expiry.md` with the dated commands and outputs: expired while stopped (yes/no), and when. If backups do NOT expire while stopped, the doc states the consequence for the promise wording and proposes a fix for Keshav to decide (for example `demo-up` deleting expired backups explicitly); it does not change the arch. Out of scope: implementing any fix, production instances.

## Acceptance criteria
- [ ] Given the non-prod instance and a recorded retention value, when the spike ends, then `docs/adr/cloud-sql-backup-expiry.md` exists with the raw `gcloud sql backups list` output at the three time points.
- [ ] The doc states a one-line verdict ('expires while stopped' or 'does not expire while stopped') that is checkable against the pasted output.
- [ ] The instance is deleted at the end (`gcloud sql instances list` shows none for the spike) and no prod resource is touched.
- [ ] The doc names the promise sentence of deep-dive/04-2 4.19 'Backups: within 7 d, plus ledger replay' as confirmed or needing change.
