---
key: "E14-T3"
title: "reflexion.txt + reverification.txt prompts"
epic: "E14"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: []
arch_refs: ["deep-dive/04-agent-pipeline.md#4.3", "deep-dive/00-poc-and-the-pivot-to-mvp.md#0.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 70, "id": 5694998891, "url": "https://github.com/Keshav0375/sentinel-brain/issues/70"}
branch: "dev/backend-phase-4-agents"
pr: "https://github.com/Keshav0375/Sentinel/pull/22"
updated: "2026-11-08"
---

## Summary
Add the two new agentic-loop prompts as files (loaded at runtime; LangFuse-first per §6.3).

## Description
Source: backend task 4.3 (`sentinel-brain/implementation/tasks/backend/phase-4-agents/task-3-reflexion-reverification-prompts.md`).

**Files created:**
- `src/sentinel/agents/prompts/reflexion.txt` — the critique prompt (§4.3): confidence 0.0–1.0, supporting/missing evidence, next tool call if < 0.7.
- `src/sentinel/agents/prompts/reverification.txt` — the PASS/FAIL/ESCALATE check (§4.4): fix addresses root cause? target deploy correct? side effects?
- Follow CLAUDE.md prompt rules: role first line, output-format expectations, constraints, < 800 tokens.

## Acceptance criteria
- [x] Both prompts exist, load via the prompt loader with file fallback, and specify the exact output contract the orchestrator parses (confidence float; PASS/FAIL/ESCALATE token).
- [x] Under 800 tokens each; no hardcoding in code.

## Outcome
Built `reflexion.txt` (~731 tok) and `reverification.txt` (<800 tok). Commit d324296 `feat: reflexion + reverification prompts, output contracts, preamble on the LangFuse path`.
ReflexionResult JSON contract: next_tool_call restricted to analysis tools; SuspectDeploy when a specific deploy is identified. Reverification is a strict one-line token: PASS | FAIL: r | ESCALATE: r; parser sends anything else to ESCALATE.
`infra/tracing.load_prompt` appends UNTRUSTED_DATA_PREAMBLE on both branches (returns a TextPromptClient copy, keeps §6.3/R14 prompt link; single source in agents.loader). Fake-LLM turns for both.
