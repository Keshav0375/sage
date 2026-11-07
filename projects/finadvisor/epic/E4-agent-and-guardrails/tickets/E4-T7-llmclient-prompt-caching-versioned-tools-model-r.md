---
key: "E4-T7"
title: "LLMClient: prompt caching, versioned tools, model retirement check"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T5", "E4-T3"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#ADR-006", "deep-dive/06-interfaces-and-contracts.md#6.1"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 99, "id": 6155686022, "url": "https://github.com/Keshav0375/FinAdvisor/issues/99"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Cache system prompt plus tools, version them with PROMPT_VERSION and fail readiness on retired models.

## Description
Place cache_control at the end of tools then system (cache order tools, system, messages); tenant/user/date text only in messages after the breakpoint. Tool definitions and system prompt are built by one function keyed on PROMPT_VERSION; a test hashes them so a change without a PROMPT_VERSION bump fails CI. Apply the spike (E4-T3) result: if the prefix is under the model minimum, log a warning with token count. Add a retirement table (model id -> retirement date) in config and a check used by /readyz (model availability item, 6.1) and a CI test that fails when a configured model is retired or retires within 30 days. Record cache_read/creation tokens in usage. Quote ADR-006: 'tool definitions are versioned with the prompt because changing them invalidates the cache'.

## Acceptance criteria
- [ ] Given two consecutive requests with the same prefix against the stub, when built, then the system/tools blocks are byte-identical and carry cache_control; tenant/user/date text appears only after the breakpoint (test).
- [ ] Given a tool schema edited without a PROMPT_VERSION bump, when CI runs, then the hash test fails.
- [ ] Given LLM_MODEL_ANSWER set to a retired id, when /readyz is called, then it reports not ready; and the CI retirement test fails for a model retiring within 30 days.
- [ ] Usage events include cache_read_input_tokens and cache_creation_input_tokens.
