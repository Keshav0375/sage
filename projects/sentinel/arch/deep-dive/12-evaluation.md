> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 12. Evaluation

### 12.1 Judge

- Scores the quality of the reasoning, not the outcome: a well-evidenced escalation of an ambiguous
  root cause scores well; a rollback of the wrong deploy scores poorly.
- Rubric anchored on ground truth from `branches.yaml`: triage = `expected_signal_type` (+
  `expected_failed_stage`); root cause = `fault` / `expected_culprit`; remediation =
  `expected_resolution` + `expected_culprit`.
- Every dimension is a NUMERIC score in [0, 1].
- Judge model: a model no agent role uses, primary or fallback (`gpt-4.1` when Anthropic is primary,
  `claude-opus-4-1` when OpenAI is primary); a static check plus a runtime guard marks any run whose
  `models_used` contains the judge as `judge_conflict`. A judge failure is `judge_failed`. Both flags
  are stored and never aggregated. The judge has no fallback and is never cached.
- History: the POC default judge was the triage model; the 2026-10-15 rule (judge = the other
  provider's `gpt-4o`) still self-graded because `gpt-4o` is the fallback model
  ([ADR-035](../decision-logs.md#adr-035)).

### 12.2 Runner and dataset

- The pipeline writes one item to the Langfuse dataset `sentinel-scenario-runs` at the terminal
  state, with the branch label (the PR's head ref, validated against the catalog), PR number, merge
  SHA and the status-only trajectory.
- `scripts/run_eval.py` is a **read-only scorer**: backend code never merges, deploys or reverts
  scenario branches. A human runs a scenario by merging its PR; GHA deploys; Sentinel drafts the
  revert PR; the runner reads the finished trajectories, joins each item to the vendored
  `branches.yaml`, and scores four checks (fired, classified, correlated, revert-PR target) plus the
  judge dimensions.
- Output: Langfuse scores, `incidents.eval_score` JSONB
  (`{judge_model, judge_conflict, scores, reasoning}`), and the report served by `GET /api/eval-report`.
- Offline tests use a vendored copy of `branches.yaml` that must stay in sync with
  `Sentinel-deployment/scenarios/branches.yaml`.

### 12.3 In-cluster eval

`ci_eval.yml` (dispatch only, [ADR-045](../decision-logs.md#adr-045)) runs `run_eval.py` as a
Kubernetes Job in `sentinel-dev` under the backend's workload identity, so the LLM keys stay in the
pod and no GHA identity can read them. The namespace quota is one backend pod, so the eval pauses the
backend (backend-up, scale to 0, Job, restore per keep-warm); incidents queue in the `sentinel-backend`
concurrency group meanwhile. Reports leave through the Job logs between markers. One `eval.scored`
event per scenario branch per run (newest item only). Needs the pending infra CI-identity ticket to
grant gha-backend `batch/jobs` create/get/list/watch/delete and `pods`, `pods/log` read in `sentinel-dev`.

### 12.4 Status

The eval has been run only offline (fake LLM, stubbed Langfuse). No live scenario run exists yet, so
there are no real scores. See [15](15-open-questions.md).
