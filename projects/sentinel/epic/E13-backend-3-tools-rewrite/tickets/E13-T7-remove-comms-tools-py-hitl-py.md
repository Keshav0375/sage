---
key: "E13-T7"
title: "Remove comms_tools.py + hitl.py"
epic: "E13"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E13-T6"]
arch_refs: ["deep-dive/04-agent-pipeline.md#4.4", "deep-dive/00-mvp-phase-1-and-the-pivot.md#0.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 66, "id": 5694998292, "url": "https://github.com/Keshav0375/sentinel-brain/issues/66"}
branch: "dev/backend-phase-3-tools"
pr: "https://github.com/Keshav0375/Sentinel/pull/21"
updated: "2026-11-08"
---

## Summary
Delete the two tools that no longer exist in Phase 2: notifications are done by GHA;

## Description
Source: backend task 3.7 (`sentinel-brain/implementation/tasks/backend/phase-3-tools/task-7-remove-comms-and-hitl-tools.md`).

HITL is the GitHub PR, not a tool. Update the tool registry + any imports.

**Files deleted:** `src/sentinel/tools/comms_tools.py`, `src/sentinel/tools/hitl.py`.
**Files modified:** tool registry / `__init__`, orchestrator wiring, tests that referenced them.

**⚠ Order:** do this only after 3.2–3.6 land, so nothing imports the removed tools mid-phase.

## Acceptance criteria
- [x] Both files removed; no dangling imports; app boots; tool registry lists exactly the six Phase-2 tools (§3 Tools).
- [x] No `request_human_approval` / execute path remains (safety invariant).

## Outcome
Removed `comms_tools.py` and `hitl.py`. Commit `87b4a11` (refactor: remove comms_tools, hitl and all approval plumbing).
- Removed ApprovalFn and approve_hitl (POST /approve -> 404), dashboard approval UI, HitlGateRegistry and HITL event types, ApprovalRequest/Result, ApprovalStatus/RiskLevel, eval auto-approve.
- Registry holds exactly six tools; remediation agent has only prepare_rollback_spec + format_escalation; comms agent has zero tools. Prompts, remediation_safety rubric and README reworded.
- Gate: VERDICT GREEN (7 ran). Grep for removed names in src/ and tests/ returns 0 hits.
- Left for phase 4: the "pending_approval" status vocabulary.
