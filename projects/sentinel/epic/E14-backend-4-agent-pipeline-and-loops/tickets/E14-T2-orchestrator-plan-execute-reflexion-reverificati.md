---
key: "E14-T2"
title: "Orchestrator: plan-execute + reflexion + reverification + budget"
epic: "E14"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E14-T1", "E14-T3"]
arch_refs: ["deep-dive/04-agent-pipeline.md#4.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 69, "id": 5694998738, "url": "https://github.com/Keshav0375/sentinel-brain/issues/69"}
branch: "dev/backend-phase-4-agents"
pr: "https://github.com/Keshav0375/Sentinel/pull/22"
updated: "2026-11-08"
---

## Summary
Rewrite the orchestrator from a linear chain to plan-execute with reflexion + reverification

## Description
Source: backend task 4.2 (`sentinel-brain/implementation/tasks/backend/phase-4-agents/task-2-orchestrator-loops.md`).

loops and a hard tool-call budget (§4.1–4.6).

**Files modified:** `src/sentinel/agents/orchestrator.py` (+ triage/analysis/resolution agent wiring as needed).
- **Plan-execute:** orchestrator plans agent order after triage.
- **Reflexion:** after analysis, critique step; if confidence < 0.7 loop back with guidance, **max 2 loops** (§4.3).
- **Decision gate:** confidence ≥ 0.7 AND root cause = specific deploy → Resolution; else Escalate (§4.2).
- **Reverification:** after resolution, PASS/FAIL/ESCALATE; FAIL → 1 retry; ESCALATE → escalate (§4.4).
- **Budget:** hard cap **20** tool calls; exhaustion → escalate with gathered context (§4.6).
- Records `reflexion_loops`; produces the response fields the webhook returns.

## Acceptance criteria
- [x] Reflexion loops capped at 2; tool-call budget enforced at 20; both observable in output/trajectory.
- [x] Decision gate + reverification implemented; escalation path returns full context.
- [x] Judge scores both paths (wired in Phase 6).

## Outcome
Built the Python orchestrator: plan by signal_type (deploy_failure fast path), reflexion (<=2 loops), confidence>=0.7 + specific-deploy gate, RollbackSpec cross-check vs deployments, reverify FAIL <=1 retry, per-incident 20-call budget (incl. parallel/fallback) -> escalate. Six agents (triage, analysis, reflexion, resolution, reverification, pr_content_generator). PipelineResult{rollback_proposed|escalated, tool_calls_used, tokens_used, models_used}; persistence via store_incident(IncidentOutcome), persist=False for eval/run_scenario.
Commits: 3e4e239 (orchestrator), a3a1dd8 (store pipeline outcome).
Tests/gate: VERDICT GREEN, 7 ran (orchestrator: env -i + TEST_DATABASE_URL); fake LLM + real Postgres; boot with no keys proven.
Verify: run the orchestrator tests with env -i and TEST_DATABASE_URL set; `poetry run sentinel serve` boots with no keys.
