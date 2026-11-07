---
key: "E8-T3"
title: "Add Identity Platform tenant sign-in with in-memory token"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T2", "E1-T21"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.2", "decision-logs.md#adr-010", "deep-dive/06-interfaces-and-contracts.md#6.1"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
An advisor signs in to their firm's IdP tenant and API calls carry the ID token, never persisted to localStorage.

## Description
Implements deep-dive/08-security-and-privacy.md §8.2 steps 2-3 and ADR-010. Use the Firebase/Identity Platform web SDK: set `auth.tenantId = idp_tenant_id` from E8-T2, email/password sign-in, token from `getIdToken()` kept only in memory (SDK auth persistence set to `inMemoryPersistence`; no localStorage/sessionStorage/IndexedDB or cookie for the token). Build an `apiFetch` wrapper that adds `Authorization: Bearer <token>` and refreshes via getIdToken. After sign-in call `GET /v1/me` and store {advisor_id, display_name, role, tier}. Provide sign-out. Remove the MVP UserSwitcher/X-User header flow. Config: Firebase web config via Vite env (VITE_*), no secrets. Out of scope: SSO, tenant onboarding (E1/E10), 401 UI handling (E8-T4).

## Acceptance criteria
- [ ] Given a signed-in session in a vitest test with a mocked SDK, when apiFetch is called, then the request has `Authorization: Bearer <token>`.
- [ ] Given sign-in completes, when localStorage, sessionStorage and document.cookie are inspected, then none contains the token string (unit test; repeated in Playwright E8-T11).
- [ ] Given the SDK auth instance, when initialised, then tenantId equals the discovered idp_tenant_id and persistence is in-memory (unit test).
- [ ] Given sign-out, when called, then the in-memory token and /v1/me state are cleared and the sign-in form shows.
- [ ] grep of src/ finds no `X-User` header or UserSwitcher.
