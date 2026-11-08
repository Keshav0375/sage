> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 15. Open questions and unverified behaviour

Nothing below is a design gap in the shipped code; each is a live behaviour that has not run yet,
or an owner decision.

### 15.1 Never run live

- **The end-to-end demo.** No scenario has gone through the real path (merge, Datadog, bridge,
  `repository_dispatch`, `ci_incident_response.yml`, revert PR). Runbook: `sentinel-brain/reports/DEMO.md`
  (pass/01, deployfail/03, runtime/01, optional runtime/07).
- **Real LLM calls.** Every agent phase was verified on the fake LLM; B4/B5 (Anthropic and OpenAI
  keys in Key Vault) are open.
- **Live eval.** No real scores; needs scenario runs plus `ci_eval.yml` with the Job RBAC.
- **Backend on AKS.** Apply, LB IP, backend-up/down, startup vs liveness (there is no startupProbe),
  and `automountServiceAccountToken: false` with workload identity have not been seen live.
- **Pause/Resume** (`infra_pause`): zero runs; `gha-ops` and the `ops` environment never authenticated.
- **Memory hardening:** backup, restore, checkpoint resume and Redis not exercised against Azure.
- **Dashboard:** GitHub Pages not enabled, so the site is not published.
- **Deployment carry-overs:** `runtime/07` mtime anchor unproven; re-run `datadog/apply.sh` after the
  next apply (new synthetic assertions); the "old version still serving" strings in
  `ci_app_deployment.yml` need a PR merged while the estate is up.

### 15.2 Pending owner steps

See [../../state.md](../../state.md) "Now" for the ordered list (Pages, identity re-bootstrap,
DB grants, the infra CI-identity ticket, `REVERT_PR_PAT`, real LLM keys, estate up, demo).

### 15.3 Open decisions and follow-ups

- Should the four repos stay public (ids in old docs and logs)?
- Re-check the filelock pip-audit ignores by 2026-11-24.
- Remove `EventBus` / `DashboardEventEmitter` (no subscriber since the SSE route was removed).
- The Redis `aclose` wait sits outside the shutdown grace budget.
- The restore's placeholder UPDATE should also set `resolution_type` and `resolved_at`.
- The memory-restore `terraform output` errors are silent.
- The `sentinel-backend` concurrency group holds one pending run; a burst of alerts would need a queue.
- The 50K-token alert has no sink beyond a structured warning.
- Backend phases 10-11 and infra phase 7 were built from user tickets but are not yet in the
  tracker (`/new-ticket`).
