---
key: "E16-T1"
title: "eval/judge.py → LangFuse scores"
epic: "E16"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E12-T4", "E14-T2", "E14-T1"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 80, "id": 5695000391, "url": "https://github.com/Keshav0375/sentinel-brain/issues/80"}
branch: "dev/backend-phase-6-eval"
pr: "https://github.com/Keshav0375/Sentinel/pull/24"
updated: "2026-11-08"
---

## Summary
Judge scores trajectory quality on both rollback and escalation paths; scores pushed to

## Description
Source: backend task 6.1 (`sentinel-brain/implementation/tasks/backend/phase-6-eval/task-1-judge-langfuse-scores.md`).

LangFuse and stored on the incident row (`eval_score` JSONB).

**Files modified:** `src/sentinel/eval/judge.py`
- Judge agent (model per §4.7 / dec 2026-10-18, **different family/model discipline** from graded agents — safety invariant) scores per-dimension (triage_accuracy, root_cause_correctness, etc.).
- `push_score(trace_id, name, value)` per dimension (§6.4); return structured `JudgeResult`.
- Evaluates reasoning quality, not outcome (§3): good escalation can score well.

## Acceptance criteria
- [x] Scores both paths; per-dimension values in [0,1]; pushed to LangFuse; stored on incident.
- [x] Judge model distinct from the agents it grades (no self-eval).

## Outcome
Built in Sentinel commit faf7412 on dev/backend-phase-6-eval: "refactor: eval judge scores 0-1, pushes one LangFuse score per dimension, stores incidents.eval_score". Both outcomes judged; conflict stored but not pushed; eval_score shape `{judge_model, judge_conflict, scores, reasoning}`. Judge not wired into live pipeline (6.2 runner is the scorer; dec 2026-10-22, brain 1ffd083).
Files: models/eval_result.py; eval/{rubric,judge,report,runner}.py; memory/episodic.py (new store_eval_score); dashboard/eval.html; scripts/run_eval.py; tests.
Review fix batch cf56e67 ("fix: eval judge anchors on branches.yaml, flags judge failures, runner stores incidents.eval_score"; decisions brain 1ffd083, a85666d): rubric re-anchored on the branches.yaml fields; `judge_failed` flag (stored in eval_score, never pushed to LangFuse or aggregated); untrusted-data preamble plus `<trajectory>`/`<ground_truth>` tags; no-secrets instruction for reasoning.
