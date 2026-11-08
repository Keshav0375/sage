---
key: "E13-T6"
title: "prepare_rollback_spec + format_escalation"
epic: "E13"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E13-T1"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 65, "id": 5694998132, "url": "https://github.com/Keshav0375/sentinel-brain/issues/65"}
branch: "dev/backend-phase-3-tools"
pr: "https://github.com/Keshav0375/Sentinel/pull/21"
updated: "2026-11-08"
---

## Summary
Replace Phase-1 `draft_rollback_pr` (mock PR payload) with **output-only** tools — the

## Description
Source: backend task 3.6 (`sentinel-brain/implementation/tasks/backend/phase-3-tools/task-6-remediation-and-escalation.md`).

backend never calls GitHub; GHA creates the PR (§3.3 "backend reasons, GHA executes").

**Files modified:** `src/sentinel/tools/remediation_tools.py`
- `prepare_rollback_spec(...)` → `RollbackSpec{target_commit_sha, justification, evidence_summary, confidence}`. **No external calls.**
- `format_escalation(...)` → `EscalationContext{hypothesis, evidence, confidence, missing}` for Teams.
- Both `@function_tool`, typed, pure (no side effects), structured errors.

## Acceptance criteria
- [x] Neither tool performs I/O to GitHub/Teams (safety invariant: no tool touches external state).
- [x] Outputs match the shapes consumed by the webhook response + `/generate/pr-content`.

## Outcome
Built `prepare_rollback_spec` and `format_escalation`; removed `draft_rollback_pr`/`draft_hotfix`. Commit `fc89e7f` (refactor: prepare_rollback_spec and format_escalation replace the draft tools).
- RollbackSpec is the section 3.4 /generate/pr-content body field-for-field (TARGET_SHA = target_deploy.commit_sha); EscalationContext{hypothesis, evidence, confidence, missing}.
- Both pure (socket/httpx/asyncpg patched to raise, plus AST import check). Validation: sha 7-40 hex lowercased, pr>=1, tz-aware deployed_at, confidence 0..1. No confidence gate (orchestrator rule, phase 4).
- Tests: 44. Gate: VERDICT GREEN (7 ran, env -i + TEST_DATABASE_URL). Tree clean, attribution none.
- Verify: `pytest tests/test_tools/test_remediation_tools.py -q`
