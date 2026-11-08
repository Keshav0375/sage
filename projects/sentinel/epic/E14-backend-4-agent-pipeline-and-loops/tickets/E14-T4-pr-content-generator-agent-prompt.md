---
key: "E14-T4"
title: "pr_content_generator agent + prompt"
epic: "E14"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E14-T1"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.3"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 71, "id": 5694999037, "url": "https://github.com/Keshav0375/sentinel-brain/issues/71"}
branch: "dev/backend-phase-4-agents"
pr: "https://github.com/Keshav0375/Sentinel/pull/22"
updated: "2026-11-08"
---

## Summary
The agent that writes the **rollback** PR title + description during an incident (the only

## Description
Source: backend task 4.4 (`sentinel-brain/implementation/tasks/backend/phase-4-agents/task-4-pr-content-generator.md`).

consumer is `ci_incident_response.yml`). No tools — pure constrained generation, Haiku.

**Files created:**
- `src/sentinel/agents/pr_content_generator.py` — Agent def, model `anthropic/claude-haiku-4-5` (fb `openai/gpt-4o-mini`), no tools, traced as `pr-content-generation` span.
- `src/sentinel/agents/prompts/pr_content_generator.txt` — per §3.4 key instructions: title `revert:` prefix < 72 chars with PR# + incident id; description sections Incident/Root Cause/Evidence/Rollback; state confidence plainly; 100–200 words.

## Acceptance criteria
- [x] Given the §3.4 input (root_cause, evidence, confidence, target_deploy) produces `{title, description, model_used, tokens_used}`.
- [x] Title format + description sections match §3.4; no tools attached.

## Outcome
Built `pr_content_generator` agent + prompt (commit 98751f8, Sentinel, feat: pr_content_generator agent + prompt — §3.4 revert PR title and description). No tools; router haiku (fb gpt-4o-mini) via call_with_fallback; Langfuse prompt loader linked via use_agent_prompts; span `pr-content-generation`, no IO. RollbackSpec -> PRContent{title, description, model_used, tokens_used}. Title (revert:, PR #, incident id, <72) and description (4 sections, confidence, 100-200 words) rules enforced in code with deterministic fallbacks. Plain-text reply. Not yet wired to an endpoint (phase 5).
