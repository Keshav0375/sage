> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 10. Security and HITL invariants

These are the invariants the `safety-reviewer` agent checked on every backend phase and on any
diff touching tools, agents, the orchestrator, the API, memory, eval, identities or workflows.

### 10.1 HITL: the revert PR is the gate

- **No backend tool modifies external state.** The backend reasons and drafts; GitHub Actions
  executes; the revert PR on `Sentinel-deployment` is the human gate. A tool that would act on the
  world is a design error to restructure, not to guard.
- **Fire-and-forget.** Sentinel's job ends when the revert PR exists and Teams is notified (or the
  escalation is sent). No waiting state, no merge/close tracking, no `/approvals` endpoint.
  `mttr_seconds` measures alert to decision, not human review.
- **No workflow can merge.** `Sentinel-deployment` `main` requires a PR; `REVERT_PR_PAT` can push
  only `revert-<sha>` and open the PR; nothing enables auto-merge or approves.
- **The pipeline never auto-rolls back.** Rejected on purpose for verify-stage failures: GHA would
  remediate on its own and bypass the human ([ADR-031](../decision-logs.md#adr-031)).
- **The dashboard only observes.** No UI action merges or approves anything.
- Writes the backend does make are to its own stores only: Postgres (`incidents`,
  `deployments.incident_id`, checkpoints, cache), Langfuse traces, scores and dataset items.

### 10.2 Agentic safety caps

Tool-call budget 20 per incident across all runs; reflexion at most 2; reverification retry at most
1; confidence gate 0.7; target SHA cross-checked against `deployments` and the merge commit; a
resume carries every cap and an absolute deadline; untrusted-data preamble on every prompt (also on
the Langfuse prompt path); tool outputs size-capped; `pr_details.branch` (the ground-truth label)
never reaches an agent prompt; judge model distinct from every agent model with a runtime
`judge_conflict` guard; the judge prompt treats the trajectory as untrusted and never quotes secrets
or raw log values.

### 10.3 R14: what leaves our stores

- Langfuse generations carry model, token usage and the prompt-version link, never inputs or
  outputs; `observe` defaults to no input/output capture.
- The openai-agents default trace exporter (which uploaded full spans with tool and log data to
  OpenAI whenever an OpenAI key was set) is removed; startup sets exactly Sentinel's processors once,
  with `trace_include_sensitive_data=False`.
- Narrow exception: Langfuse dataset items carry the LLM-written root cause, evidence summary and
  justification, with every raw tool output and log clip stripped; the trajectory is status-only.
- Cached rows stay in our DB and are never exported. The public dashboard carries allow-listed
  fields only, LLM summaries capped at 500 characters, and gitleaks runs on the ledger.

### 10.4 Least privilege

- CI identities split by reachability, not scope ([09-1](09-1-identity-plane.md#99-ci-identities)).
- The backend's GitHub PAT has Pull requests: read on `Sentinel-deployment` only; the Datadog app key
  is scoped to `logs_read_data` and `synthetics_read`.
- DB principals: `gha-app` INSERT/SELECT on `deployments`; the gha-backend principal (pending ticket)
  SELECT on `services`, `SELECT(id)` + `UPDATE(pr_number, pr_url)` on `incidents`; `gha-deploy` scoped
  to one database with a column-level UPDATE.
- The pod: read-only root filesystem, non-root, no auto-mounted SA token, NetworkPolicy, ConfigMap only.
- PR-triggered workflows get `contents: read`, no environment, no `id-token`, no secrets
  (`pull_request`, never `pull_request_target`); no PR-triggered job writes to the ledger.

### 10.5 Supply chain and CI hygiene

Every third-party action pinned by commit SHA; composite actions used cross-repo by SHA; the image base
by digest and the embedding model by revision; installs from lockfiles; pip-audit, gitleaks, ruff,
pyright in the gate; untrusted text reaches `run:` only via `env:` or files (the
`guard-main-source.yml` `head_ref` injection was found and fixed in backend phase 8); SQL values only
as `psql -v` variables (PR titles and authors are attacker-influenced). A dated pip-audit exception
covers 13 filelock CVEs that litellm's `<4.0` cap blocks (re-check 2026-11-24).

### 10.6 Known gaps (stated, not hidden)

- All four repos are public; subscription and tenant ids appear in old docs and run logs. Neither
  authenticates anything; whether the repos should be public is an open owner decision.
- The Postgres firewall allows all in dev; the backend LB IP is public.
- Infra PRs do not run tflint, shellcheck or gitleaks in CI (owner trade-off, [ADR-027](../decision-logs.md#adr-027)).
- The live `plan-pull-request` federated credential must be deleted by hand once.
- `gha-ops` cannot-delete is proven by role inspection, not by a refused delete.
