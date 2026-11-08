# sentinel: state

## Now
- 2026-11-08 PORTED to Sage from the `sentinel-brain` control plane: arch (architecture, diagram,
  45 ADRs, 18 deep-dive files), 21 epics and 83 tickets (72 from the tracker, 11 reconstructed from
  PRs #32, #33, #35), library (sources, glossary, research notes). The brain stays the source of truth.
- 2026-10-30 ALL PLANNED BUILD WORK MERGED. Backend phase 11 merged into `Sentinel` `main` (PR #35,
  ba78355): memory hardening (checkpoints and bounded resume, tool/LLM cache, Azure Managed Redis B0,
  fail-closed pre-destroy backup, data-only restore), in-cluster eval (`ci_eval.yml`), the README.
- 2026-10-28 Infra phase 7 (monorepo, PR #32, dabf404) and backend phase 10 (ops dashboard, PR #33,
  ef6ccf0) merged.
- 2026-10-25 MVP RELEASED: `release-phase-2` merged into `main` (PR #29, merge commit);
  `main-backup` keeps the old `main`; `release-phase-2` frozen. 18/18 tracked phases signed,
  71/72 tracked tasks verified (infra 6.8 Pause/Resume shipped but never executed).
- NOT RUN LIVE: the end-to-end demo, real LLM calls, the live eval, the backend on AKS, Pause/Resume,
  memory backup/restore against Azure, the dashboard on Pages. The estate is destroyed (only
  `rg-sentinel-bootstrap` remains).
- Owner steps before anything runs live (from `sentinel-brain/implementation/STATE.md`, Next Action):
  1. Enable GitHub Pages on `Sentinel` (4 `gh api` commands), then `gh workflow run ops_pages.yml`.
     Dashboard: https://keshav0375.github.io/Sentinel/ (not live until then).
  2. `infra/scripts/bootstrap-identities.sh`, fill `infra/.env`, run `set-gh-secrets.sh`, set the repo
     variable `INFRA_OIDC_READY=true`.
  3. `infra/scripts/grant-db-access.sh` (after `alembic upgrade head`).
  4. The infra CI-identity ticket (`/new-ticket`): gha-backend federated credential and grants,
     including the eval Job RBAC.
  5. `REVERT_PR_PAT`; real Anthropic and OpenAI keys in Key Vault (blockers B4, B5).
  6. Estate up, then the live demo (`sentinel-brain/reports/DEMO.md`).
  Then archive `Sentinel-infra` after the first infra plan run from `Sentinel` passes.
- Follow-ups: re-check the filelock pip-audit ignores by 2026-11-24; remove `EventBus` /
  `DashboardEventEmitter`; the Redis `aclose` wait sits outside the shutdown grace budget; the
  restore's placeholder UPDATE should also set `resolution_type` and `resolved_at`; the memory-restore
  `terraform output` errors are silent; delete the stale `plan-pull-request` federated credential on
  `gha-plan` once; add infra 7 and backend 10-11 to the tracker with `/new-ticket`.

## Open decisions
- Production readiness (multi-tenancy, HA, TLS, GitHub App, SSO, SLOs, DR, model governance) is a roadmap, not
  built: [arch/path-to-production.md](arch/path-to-production.md).
- Should the four repos stay public? Subscription and tenant ids appear in old docs and run logs
  (neither authenticates anything).

## Blockers
- B4 Anthropic API key (backend LLM calls; Key Vault seed). Owner.
- B5 OpenAI API key (fallback and judge; Key Vault seed). Owner.

## Resume command
- Live verification, from `sentinel-brain`: follow the owner steps above, then
  `reports/DEMO.md` (pass/01, deployfail/03, runtime/01), then `ci_eval.yml`.
- New work: `/new-ticket` in `sentinel-brain`, then `/implement-phase <cat>-<M>`.
