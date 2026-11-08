# sentinel: glossary

| Term | Meaning |
|---|---|
| `sentinel-brain` | the control plane repo: architecture, decisions, tracker, task specs, reports, agents and skills; no application code |
| Phase 1 / MVP | the May 2026 local SQLite and synthetic-data prototype; replaced wholesale ([00](../arch/deep-dive/00-mvp-phase-1-and-the-pivot.md)) |
| Phase 2 | the shipped system; released 2026-10-25 |
| category | one code repo's track: infra, deployment, backend |
| phase (source) | one branch + one PR in a code repo, e.g. backend phase 5; a Sage epic here |
| task (source) | one PR-sized commit with tests; a Sage ticket here |
| case i / ii / iii | clean pass / deploy fails / runtime error: the three scenario classes |
| scenario branch | one of 30 pre-authored branches (`pass/*`, `deployfail/*`, `runtime/*`) in `Sentinel-deployment` |
| `branches.yaml` | the ground-truth catalog of the 30 branches; also the eval set |
| `signal_type` | `deploy_failure` or `runtime_error`, stamped by the bridge Function; selects the backend path |
| bridge | the Azure Function that turns a Datadog alert from Event Grid into `repository_dispatch` |
| `correlation_id` | the id minted at the bridge and carried through every hop to the trace and the Teams card |
| revert PR | the PR GHA opens on `Sentinel-deployment` to revert the culprit merge; the human gate |
| HITL | human in the loop: the backend reasons, GHA executes, a human merges or closes |
| fire-and-forget | Sentinel does not track the revert PR after creating it |
| reflexion | the self-critique loop after analysis (confidence < 0.7, at most 2) |
| reverification | the check that the rollback spec matches the root cause |
| rollback spec | `RollbackSpec`, the drafted revert target and justification |
| `rollback_proposed` / `escalated` | the two terminal incident statuses |
| judge conflict | an eval run whose models include the judge model; never counted |
| R14 | the rule that no raw tool output or log data leaves Sentinel's own stores |
| R-item | a reconciliation: a decision the owner owes before a task can proceed |
| C-item | an architecture conflict found by the warden before code |
| B-item | an external blocker |
| platform layer | shared ACR, one AKS cluster, shared Postgres (one Terraform state) |
| deployment layer | per-deployment resources in their own state, e.g. `sentinel-dev` |
| `gha-plan` / `gha-deploy` / `gha-ops` / `gha-app` | the four CI managed identities |
| identity tenant | the personal Entra tenant holding the two app registrations |
| workload identity | AKS federation of a pod's ServiceAccount token to a managed identity |
| keep-warm | `SENTINEL_KEEP_WARM=true`: skip teardowns during a demo session |
| scale-to-zero | backend Service deleted and Deployment at 0 between runs; the cluster stopped when idle |
| quality gate | `quality_gate.py`; green only on `VERDICT GREEN` from a full run |
| wave | a layer of tasks with no dependencies between them, built in parallel |
| ops ledger | the append-only `ops-ledger` branch behind the dashboard |
| `release-phase-2` | the backend integration branch during Phase 2; frozen after the release |
