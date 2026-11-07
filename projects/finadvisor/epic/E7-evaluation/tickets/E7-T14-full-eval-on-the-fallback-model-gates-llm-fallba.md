---
key: "E7-T14"
title: "Full eval on the fallback model gates LLM_FALLBACK_ENABLED"
epic: "E7"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E7-T13", "E4-T27"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.6", "ADR-017", "ADR-005"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 169, "id": 6263538167, "url": "https://github.com/Keshav0375/FinAdvisor/issues/169"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Evaluate claude-sonnet-4-6 once and make enabling the fallback depend on that result.

## Description
Run `jobs eval --subset full --model fallback` using LLM_MODEL_FALLBACK (claude-sonnet-4-6) and store the result as data/eval/fallback_result.json with the gate verdict. Add a startup check in config validation: `LLM_FALLBACK_ENABLED=true` is rejected unless data/eval/fallback_result.json (or the configured eval-record location) shows pass for the same fallback model id and a prompt version equal to current PROMPT_VERSION. Quote config table: "`LLM_FALLBACK_ENABLED` ... `false` until the gate passes against it" and ADR-017: "once against the fallback model".

## Acceptance criteria
- [ ] Unit test: Settings with LLM_FALLBACK_ENABLED=true and no passing record raises at boot.
- [ ] Unit test: a passing record for a different model id or different PROMPT_VERSION still raises.
- [ ] A fallback full-run result exists in the repo with model id claude-sonnet-4-6 and the gate verdict recorded as pass or fail with numbers.
