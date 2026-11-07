---
key: "E7-T15"
title: "Add the promptfoo red-team job"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E7-T5", "E4-T27"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.1", "deep-dive/04-components-and-responsibilities.md#4.8", "ADR-017"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Run a promptfoo red team against the API as fa_eval in the redteam job.

## Description
Add a promptfoo config (pinned version) under evals/redteam/ targeting the chat API in an ephemeral environment, with plugins for prompt injection, system prompt leakage, PII, cross-tenant/BOLA-style probes and excessive agency, mapped to OWASP LLM01, LLM02, LLM06, LLM07 (arch 8.1 tests column). Add the `redteam` job entrypoint (DB role `fa_eval`, eval tenant) and a CI workflow step on the weekly workflow; a failing probe category fails the job. Out of scope: golden-set L3 (T9).

## Acceptance criteria
- [ ] `promptfoo redteam run` in CI against the stub-LLM stack produces a report artifact and exits non-zero when a seeded vulnerable prompt (test fixture) leaks the system prompt.
- [ ] Config test asserts plugins cover LLM01, LLM02, LLM06, LLM07 (named mapping in the file).
- [ ] The redteam job fails to start if the connected DB role is not fa_eval (unit test).
