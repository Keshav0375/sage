---
key: "E1-T15"
title: "Wire identity into the API: 401 and cross-tenant isolation"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T13", "E1-T14"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/08-security-and-privacy.md#8.2", "decision-logs.md#adr-010", "decision-logs.md#adr-002"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 31, "id": 6155607066, "url": "https://github.com/Keshav0375/FinAdvisor/issues/31"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
API routes obtain their Principal from the bearer token and use scoped transactions; a token for tenant A cannot read tenant B rows.

## Description
Replace the MVP identity wiring with `Depends(get_principal)` = `verify_bearer` (E1-T13) + `load_principal` (E1-T14) in `src/dependencies.py` and use `scoped_tx(principal)` for every DB access made by the existing routes (`src/api`). Errors follow deep-dive/06-interfaces-and-contracts.md §6 error codes: `UNAUTHENTICATED` (401). The `chat-api` process connects as `fa_app` (compose and settings: `DB_USER=fa_app`).

Existing MVP content-table access in `src/retrieval` and `src/agent` keeps working only through the scoped transaction (reads); any code path that INSERTs, UPDATEs or DELETEs a content table is removed or stubbed with a clear `NotImplementedError` referencing E3 / E6 (the MVP ingest is replaced there). Do not restructure the retrieval module (E3).

Tests use the same token approach as E1-T13 (Auth emulator or locally signed JWTs with a test JWKS, per the E1-T1 ADR).

Out of scope: `RetrievalService` and import-linter retrieval contract (E3), Kong header stripping and the "reaches the app unchanged" smoke test (E2), SPA sign-in (E8).

## Acceptance criteria
- [ ] Given a request with a forged, expired, wrong-audience or wrong-tenant token, when it calls any `/v1` route except the discovery route, then the response is 401 `UNAUTHENTICATED` (`tests/api/test_auth_http.py`, 4 cases against the real app with a test IdP).
- [ ] Given a valid token for tenant A advisor and data for tenants A and B in `documents`, when the advisor calls a route that lists or reads documents or chunks, then no tenant B row appears in the response (integration test with two tenants seeded through `fa_owner`).
- [ ] Given a valid token for an IdP user who has no `advisors` row, then the response is 401.
- [ ] Given the app is started, then `SELECT current_user` in a request transaction returns `fa_app`, and no route handler calls `set_config` or opens a connection other than via `scoped_tx` (static test over `src/api`).
- [ ] Given the full existing unit test suite, then `pytest` passes with tests of the removed `X-User-Id` and mock-user behaviour deleted or rewritten to bearer tokens.
