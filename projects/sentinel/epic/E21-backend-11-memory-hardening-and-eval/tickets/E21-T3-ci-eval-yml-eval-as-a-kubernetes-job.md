---
key: "E21-T3"
title: "ci_eval.yml: eval as a Kubernetes Job"
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
Bring the backend up, scale the Deployment to 0 (the namespace quota is one pod), run `scripts/run_eval.py` as a Job in `sentinel-dev` under SA `sentinel-backend`, collect the report from the Job logs, upload it, emit one `eval.scored` event per scenario branch, restore per keep-warm.

## Description
Source: backend task 11.3 (built in https://github.com/Keshav0375/Sentinel/pull/35).

Bring the backend up, scale the Deployment to 0 (the namespace quota is one pod), run `scripts/run_eval.py` as a Job in `sentinel-dev` under SA `sentinel-backend`, collect the report from the Job logs, upload it, emit one `eval.scored` event per scenario branch, restore per keep-warm.

## Acceptance criteria
- [x] LLM keys never reach a GHA identity
- [x] The backend is restored even when the Job fails
- [x] One `eval.scored` event per branch per run

## Outcome
Merged in https://github.com/Keshav0375/Sentinel/pull/35 on 2026-10-30.
