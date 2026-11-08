---
key: "E15-T5"
title: "main.py lifespan + concurrency + token auth"
epic: "E15"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E11-T2", "E12-T4", "E15-T1"]
arch_refs: ["deep-dive/03-system-context-and-boundaries.md#3.1"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 77, "id": 5694999920, "url": "https://github.com/Keshav0375/sentinel-brain/issues/77"}
branch: "dev/backend-phase-5-api"
pr: "https://github.com/Keshav0375/Sentinel/pull/23"
updated: "2026-11-08"
---

## Summary
Wire the FastAPI app: lifespan (open asyncpg pool via **Entra DB token**, load LLM keys from

## Description
Source: backend task 5.5 (`sentinel-brain/implementation/tasks/backend/phase-5-api/task-5-app-lifespan-and-concurrency.md`).

Key Vault via **workload identity**, init LangFuse at startup, close at shutdown), apply the
**Entra bearer** dependency (`require_incident_write`, task 5.6) to all non-health routes,
router registration, and structlog config.

**Files modified:** `src/sentinel/main.py`
- `lifespan` context: acquire Entra DB token + create pool (min/max from config), init KV client (workload identity), init LangFuse; teardown reverses.
- Apply `require_incident_write` (from `api/auth.py`, task 5.6) to webhooks/incidents/generate; `/health`+`/ready` exempt.
- Mount routers: webhooks, incidents, generate, health, eval.
- structlog bound with `incident_id` where applicable.

## Acceptance criteria
- [x] App boots cleanly (CLAUDE.md non-negotiable startup check) with pool + LangFuse initialized.
- [x] Token enforced on protected routes; probes open.
- [x] Graceful shutdown closes the pool (no leaked connections).

## Outcome
Built in `d0f7ae9` (`feat: app lifespan: Entra bearer on every non-probe route, optional Key Vault secrets, PG* Entra-token pool`), `src/sentinel/main.py`.
- Entra bearer on every non-probe route; `/health`, `/ready`, `/docs`, openapi stay open (§3.6).
- Optional Key Vault (`KEY_VAULT_URL`) loads Datadog + Langfuse secrets before Langfuse init; LLM keys never read from the vault.
- PG* path uses an Entra-token password callable; `DATABASE_URL` wins. `SENTINEL_DEV_OPEN_DASHBOARD` opens only dashboard pages + read APIs.
- Lifespan no longer seeds SQLite; scenario CLI/scripts/eval still use it until 9.1. New azure deps: azure-identity 1.26.0, azure-keyvault-secrets 4.11.3, msal 1.39.0.
- Live boot: /health 200, /ready 200; /incidents, POST /webhooks/incident, POST /generate/pr-content, /api/config, / all 401 without token.
Review fixes 2026-10-21 (d0f7ae9..d27a8f3, status stays done-pending-review): ebca7f8 test_database counts only its own tagged pool; d9ead3f IncidentTasks (shared with 5.1); 09ab874 Key Vault doc (secrets read once at startup, restart to rotate); 354d722 Langfuse shutdown bounded by a 5s daemon thread. Gate on d27a8f3: VERDICT GREEN (full run, 7 ran, 0 skipped, TEST_DATABASE_URL set); boot OK (/health 200, /ready 200, protected 401, clean exit).
