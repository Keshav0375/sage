---
key: "E1-T13"
title: "auth module: tenant-aware ID token verification"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T1", "E1-T22"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/08-security-and-privacy.md#8.2", "decision-logs.md#adr-010", "decision-logs.md#adr-032"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 29, "id": 6155604467, "url": "https://github.com/Keshav0375/FinAdvisor/issues/29"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
A FastAPI dependency verifies the Identity Platform ID token tenant-aware with firebase-admin and returns (sub, idp_tenant_id), replacing the X-User-Id header.

## Description
Implement the `auth` module (deep-dive/04-components-and-responsibilities.md §4.5): "verifies the `Authorization: Bearer <Identity Platform ID token>` with firebase-admin tenant-aware verification: the `firebase.tenant` claim names the IdP tenant, and `tenant_mgt.auth_for_tenant(tenant_id).verify_id_token(...)` checks signature, `aud`, `iss`, `exp` and raises `TenantIdMismatchError` on a tenant mismatch. Output: `(sub, idp_tenant_id)`. Never reads identity from headers." Fixes G-01. Follow the claim name and exception classes recorded by the E1-T1 ADR. Tests use the Firebase Auth emulator in CI if the E1-T1 ADR says it supports multi-tenancy; otherwise locally signed test JWTs with a test JWKS (as the ADR records).

Build `src/auth/verifier.py`: `async verify_bearer(authorization: str | None) -> VerifiedIdentity(sub, idp_tenant_id)`. Steps: parse the Bearer header; decode the unverified payload to read the tenant claim; get `tenant_mgt.auth_for_tenant(tenant)`; verify; the firebase-admin app is initialised from `IDP_PROJECT_ID`. Blocking firebase-admin calls run in a threadpool. Any failure (missing header, malformed token, bad signature, expired, wrong audience or issuer, `TenantIdMismatchError`, missing tenant claim) raises the app's `UNAUTHENTICATED` error mapped to HTTP 401 with a body that does not reveal the cause. Remove `src/auth/mock_users.py`, the `X-User-Id` reading and `python-jose` use (`src/auth/jwt.py`); the identity of a request is never read from any header other than `Authorization`.

Out of scope: mapping to `tenants.id` and loading entitlements (E1-T14), route wiring (E1-T15), Kong header stripping (E2).

Round 4 (ADR-032, R4-D18 V5): this ticket starts only after E1-T22 records `SAME_EMAIL_TWO_TENANTS=pass`. The verifier is project-level: it reads `firebase.tenant` from the token, checks it equals the tenant of the requested firm, and returns `(sub, idp_tenant_id)`; one token carries exactly one firm and no identity is merged across firms (a person in two firms has two `sub` values and two `advisors` rows). If E1-T22 recorded `fail`, stop and wait for the new ADR (per-firm email aliases).

## Acceptance criteria
- [ ] Given a validly signed token of tenant A with the right audience, when `verify_bearer` runs, then it returns `(sub, A's idp tenant id)` (`tests/auth/test_verifier.py`).
- [ ] Given each of: no header, `Authorization: Basic ...`, a token with a forged signature, an expired token, a token with a wrong audience, a token without the tenant claim, then `verify_bearer` raises `UNAUTHENTICATED` (6 parametrised cases) and the HTTP response is 401 with the same body for every case.
- [ ] Given a token whose tenant claim names tenant B but which is verified against tenant A's `auth_for_tenant`, then `TenantIdMismatchError` is raised inside the module and surfaces as 401 (test).
- [ ] Given a request carrying `X-User-Id: <uuid>` and no `Authorization`, when it hits a dependency using `verify_bearer`, then the response is 401; `grep -R 'X-User-Id\|mock_users' backend/src` returns nothing.
- [ ] Given `mypy` and `import-linter` run in CI, then `src/auth` imports nothing from `src/retrieval` or `src/db` content access (contract passes).
- [ ] Given two tokens for the same email, one from tenant A and one from tenant B, then `verify_bearer` returns different `sub` values and different `idp_tenant_id` values, and neither token verifies against the other tenant (`tests/auth/test_verifier.py::test_same_email_two_firms_no_merge`).
