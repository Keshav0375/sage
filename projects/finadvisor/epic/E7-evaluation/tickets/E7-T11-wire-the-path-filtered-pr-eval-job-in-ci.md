---
key: "E7-T11"
title: "Wire the path-filtered PR eval job in CI"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T14", "E7-T6", "E7-T8", "E7-T9", "E7-T10"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "ADR-017"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 166, "id": 6263530804, "url": "https://github.com/Keshav0375/FinAdvisor/issues/166"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Run the ~60-question subset as the blocking `eval` job on relevant PRs.

## Description
Add a GitHub Actions workflow `eval-pr.yml` extending the E0 CI (Postgres with pgvector and Kafka service containers already exist): path filter on backend/src/{retrieval,agent,guardrails,llm,prompts}, data/eval, and prompt files; steps: migrate, seed the eval tenant, run `jobs eval --subset pr --layers l1,l2,l3` as fa_eval, then `scripts.eval_gate`; upload result JSON as an artifact; fail the check on gate failure. Secrets for Anthropic and Voyage come from GitHub secrets; the job runs only when secrets exist (fork PRs skip with a visible neutral status). Out of scope: the weekly workflow (T13); the L0 jobs (E0/E1).

## Acceptance criteria
- [ ] On a PR touching backend/src/retrieval the workflow runs and the check named `eval` appears; on a docs-only PR it does not run (verified by a workflow path-filter test via `act` or recorded run links in the PR description).
- [ ] A forced gate failure (E7-T12 fixtures) turns the `eval` check red; the green path posts the metrics table as an artifact.
- [ ] The job's DB user is fa_eval (assert in a CI step that `select current_user` equals fa_eval).
