---
key: "E8-T3"
title: "Add Identity Platform tenant sign-in with in-memory token"
epic: "E8"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E8-T2", "E1-T21"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.2", "decision-logs.md#adr-010", "decision-logs.md#adr-032", "deep-dive/06-interfaces-and-contracts.md#6.1"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 200, "id": 6263585290, "url": "https://github.com/Keshav0375/FinAdvisor/issues/200"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
An advisor signs in to their firm's IdP tenant through one auth instance per firm, API calls carry that firm's ID token, and nothing is persisted.

## Description
Implements deep-dive/08-security-and-privacy.md §8.2 steps 2-3, ADR-010 and ADR-032: "The SPA keeps one auth instance per firm and a firm switcher; each API call carries one firm's token." Client facts (ADR-032): `currentUser` does not change when `tenantId` is switched, and `tenantId` is not persisted on reload, so the SPA must not rely on one shared auth object.

Use the Firebase/Identity Platform web SDK through a factory `getFirmAuth(slug, idp_tenant_id)` that creates (once, memoised in memory) a separate named Firebase app and auth instance per firm: `auth.tenantId = idp_tenant_id` from E8-T2, `inMemoryPersistence`, email/password sign-in, token from `getIdToken()` kept only in memory (no localStorage/sessionStorage/IndexedDB or cookie for the token and no persisted `tenantId`). `apiFetch(firmSlug, ...)` takes the firm explicitly, uses that firm's `apiBase` (E8-T2) and adds `Authorization: Bearer <token of that firm>`; it never reads another firm's instance. After sign-in call `GET /v1/me` and store {advisor_id, display_name, role, tier} per firm. Provide sign-out for one firm. Remove the MVP UserSwitcher/X-User header flow. Config: Firebase web config via Vite env (VITE_*), no secrets. Out of scope: the firm switcher UI (E8-T14), SSO, tenant onboarding (E1/E10), 401 UI handling (E8-T4).

## Acceptance criteria
- [ ] Given a signed-in firm A in a vitest test with a mocked SDK, when apiFetch('a', ...) is called, then the request has `Authorization: Bearer <token A>` and goes to A's apiBase.
- [ ] Given firm A and firm B signed in through `getFirmAuth`, when B's auth `tenantId` is set and B signs in, then A's `currentUser` is unchanged and `getFirmAuth('a') !== getFirmAuth('b')` (unit test `firmAuth.test.ts::separate_instances`).
- [ ] Given sign-in completes, when localStorage, sessionStorage, IndexedDB and document.cookie are inspected, then none contains the token string or a tenantId value (unit test; repeated in Playwright E8-T11).
- [ ] Given each auth instance, when initialised, then tenantId equals its discovered idp_tenant_id and persistence is in-memory (unit test).
- [ ] Given sign-out of firm A, when called, then A's in-memory token and /v1/me state are cleared, firm B's session is untouched and A's sign-in form shows.
- [ ] grep of src/ finds no `X-User` header or UserSwitcher.
