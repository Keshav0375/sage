---
key: "E13-T11"
title: "Multiple logins: two firms, one token each, alias fallback"
epic: "E13"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E13-T5", "E1-T1", "E1-T21"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.2", "deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4", "decision-logs.md#adr-032"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
One person can hold an account in two firms with one token per firm and no identity merge; if the E1 same-email spike failed, onboarding uses per-firm aliases.

## Description
Implements ADR-032: "One Identity Platform tenant per firm, one `advisors` row per `(tenant_id, idp_uid)`, one token per firm, no identity merge ... Linking one person across firms is optional, opt-in UX, never an authorization input. If [the spike] fails, onboarding uses per-firm email aliases" (08 §8.2 step 8).

Read the E1-T1 / same-email spike result (ADR addendum in `docs/adr/`). Branch on it:
- Passed: add an integration test and onboarding runbook for one email in two IdP tenants: two `advisors` rows (distinct `idp_uid`), each token accepted only for its own firm (E13-T5), `advisors` never joined on email for authorization, no code path reads another firm's advisor row.
- Failed: change the onboarding script (E1-T21) and `migrate --onboard-tenant` docs so a firm user is created with a per-firm email alias (`name+<slug>@domain`); the switcher flow is not used. Record the choice in `docs/runbooks/multiple-logins.md`.
Do not build person-linking; if mentioned in the runbook it is marked opt-in UX and never an authorization input.

Out of scope: SPA switcher and `currentUser` handling (E8), identity merge, person linking.

## Acceptance criteria
- [ ] Given one email registered in IdP tenants A and B (or aliases per the spike result), when each token is used on its own firm, then both succeed and resolve to different `advisors` rows (`test_multi_login.py::test_two_firms_two_rows`, #17).
- [ ] Given token A used on firm B, then 403 or 421 (`test_multi_login.py::test_cross_firm_denied`).
- [ ] Given a static check over `backend/app`, then no authorization query joins `advisors` on `email` across tenants (`test_multi_login.py::test_no_email_join`, a grep-based test that fails if one is added).
- [ ] Given the spike recorded as failed, then the onboarding script test creates the alias user and the runbook names alias mode (`test_provision_alias.py`, skipped with a recorded reason if the spike passed).
