---
key: "E15-T6"
title: "api/auth.py — Entra bearer validation (JWKS)"
epic: "E15"
repo: "Sentinel"
size: "S"
status: "done"
depends_on: ["E11-T1", "E3-T5"]
arch_refs: ["deep-dive/09-1-identity-plane.md#9.12"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 78, "id": 5695000074, "url": "https://github.com/Keshav0375/sentinel-brain/issues/78"}
branch: "dev/backend-phase-5-api"
pr: "https://github.com/Keshav0375/Sentinel/pull/23"
updated: "2026-11-08"
---

## Summary
A FastAPI dependency that validates inbound Entra JWTs statelessly and gates non-health routes.

## Description
Source: backend task 5.6 (`sentinel-brain/implementation/tasks/backend/phase-5-api/task-6-entra-bearer-auth.md`).

**Files created / changed:**
- `src/sentinel/api/auth.py` — `require_incident_write` dependency:
  - `HTTPBearer` scheme (also renders the Swagger **Authorize** button).
  - `jwt.PyJWKClient("https://login.microsoftonline.com/<tenant>/discovery/v2.0/keys")`.
  - `jwt.decode(..., algorithms=["RS256"], audience="api://sentinel-backend", issuer=<tenant issuer>)`.
  - 401 on invalid/expired/incorrect-aud/iss; 403 when `roles` lacks `Incident.Write`.
- `config.py` — read `AZURE_TENANT_ID` + `SENTINEL_API_AUDIENCE` from env (public config, from the
  `sentinel-config` ConfigMap / GitHub variables — **not** secrets).
- Wire the dependency onto `/webhooks/incident`, `/incidents*`, `/generate/pr-content`
  (via `dependencies=[Depends(require_incident_write)]` on the routers). **Leave `/health` + `/ready` open.**

**Contract:**

## Acceptance criteria
- [x] Valid `Incident.Write` token → 200; missing token → 401; valid token without the role → 403.
- [x] `/health` + `/ready` reachable with no token.
- [x] Swagger `/docs` shows an Authorize (bearer) button; authorizing attaches the token to calls.
- [x] Tenant/audience come from config, not hardcoded, not secrets.

## Outcome
Built 2026-10-18, commit 5db1a20 (from c128792): Entra bearer auth (require_incident_write); v2 JWKS of identity tenant (SENTINEL_API_TENANT_ID), audience SENTINEL_API_AUDIENCE; 401/403; pyjwt[crypto] added.
Tests: 37 added. Integrated gate (backend, env -i + TEST_DATABASE_URL): VERDICT GREEN (7 ran). Live boot: /health ok, /ready 200.
Review fixes 2026-10-21 (d0f7ae9..d27a8f3, status stays done-pending-review): ab3adea SENTINEL_API_AUDIENCE is a comma-separated list; v2 tokens carry the client-id GUID. Gate on d27a8f3: VERDICT GREEN (full run, 7 ran, 0 skipped, TEST_DATABASE_URL set); boot OK (/health 200, /ready 200, protected 401, clean exit).
