---
key: "E17-T3"
title: "Composite actions (backend-up/down, kv-secrets, teams, psql)"
epic: "E17"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E17-T2", "E3-T1", "E2-T3"]
arch_refs: ["deep-dive/07-backend-hosting-and-ci.md#7.3", "deep-dive/07-backend-hosting-and-ci.md#7.4"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 85, "id": 5695001075, "url": "https://github.com/Keshav0375/sentinel-brain/issues/85"}
branch: "dev/backend-phase-7-container-and-k8s"
pr: "https://github.com/Keshav0375/Sentinel/pull/26"
updated: "2026-11-08"
---

## Summary
The seven reusable composite actions that are the execution building blocks. Built before the

## Description
Source: backend task 7.3 (`sentinel-brain/implementation/tasks/backend/phase-7-container-and-k8s/task-3-composite-actions.md`).

workflows that use them.

**Files created (`.github/actions/*/action.yml`):**
- `backend-up` — nodepool→1, `kubectl apply -f azure/k8s/`, scale replicas→1, wait rollout, resolve LB IP, poll `/health`+`/ready`, output `backend-url` (§8.5). No static URL.
- `backend-down` — skip if `SENTINEL_KEEP_WARM=true`; `kubectl delete -f service.yaml` (release IP), replicas→0, nodepool→0.
- `get-kv-secrets` — input `names`; fetch via `az keyvault secret show`, `::add-mask::` each, one output per secret.
- `get-db-token` — `az account get-access-token --resource https://ossrdbms-aad.database.windows.net`; `::add-mask::` it; output `db-token`. Short-lived (~1 h), never stored.
- `get-backend-token` — `az account get-access-token --resource api://sentinel-backend`; `::add-mask::` it; output `api-token` for the `Authorization: Bearer` header.
- `notify-teams` — inputs title/body/severity/webhook-url → POST Teams webhook.
- `psql-exec` — inputs `sql` + **`db-token`** (from `get-db-token`, used as the psql password) → run against sentinel PostgreSQL, output `result` (JSON). **No `db-password` input.**

## Acceptance criteria
- [x] All **seven** validate under actionlint; `backend-up` outputs `backend-url`; every token/secret is `::add-mask::`ed; `backend-down` honors KEEP_WARM.
- [x] `psql-exec` accepts a token and has no password input anywhere in its interface.
- [x] Cross-repo usable (`uses: Keshav0375/Sentinel/.github/actions/psql-exec@main`).

## Outcome
Built seven composite actions (backend-up/down, get-kv-secrets, get-db-token, get-backend-token, notify-teams, psql-exec) plus `.github/actions/README.md` (pin by commit SHA, never @main). Commit 91f923b on dev/backend-phase-7-container-and-k8s.
Files: `.github/actions/*/action.yml`, `tests/test_infra/test_composite_actions.py` (54 tests, 0 skipped).
I/O per §9: pg-token, bearer, psql-exec(sql, pg-token), backend-url. Inputs reach run only via env:; all tokens masked; psql -v carries values.
backend-down honours keep-warm, deletes Service, scales to 0, never `az aks stop`. backend-up starts AKS only if stopped.
get-kv-secrets: six fixed outputs; github-pat and LLM keys excluded on purpose.
Live use needs the CI identity infra ticket (decision dd95eef) before phase 8.
