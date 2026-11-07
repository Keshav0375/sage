---
key: "E1-T21"
title: "IdP tenant provisioning script"
epic: "E1"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E1-T1", "E1-T11"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.2", "deep-dive/04-components-and-responsibilities.md#4.8", "decision-logs.md#adr-010"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 37, "id": 6155615006, "url": "https://github.com/Keshav0375/FinAdvisor/issues/37"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
A script creates the Identity Platform tenant for a firm (email/password) and prints its id for the onboarding command.

## Description
Implement the IdP onboarding script named in the scope ("IdP tenant provisioning script (Terraform comes in E10)") and deep-dive/08-security-and-privacy.md §8.2 step 7 ("IdP tenants are provisioned by an onboarding script (E1) and Terraform (E10)"). `backend/scripts/provision_idp_tenant.py --display-name <name> [--project $IDP_PROJECT_ID]`: using firebase-admin `tenant_mgt` (version pinned by E1-T1), it finds an existing IdP tenant by display name or creates one with email/password sign-in enabled, and prints the IdP tenant id (`idp_tenant_id`) on stdout (nothing else on stdout) so it can be passed to `migrate --onboard-tenant ... --idp-tenant-id`. Idempotent on display name. Does not create users and does not touch the database. Follow billing and display-name rules recorded in the E1-T1 ADR. Add a short runbook section to `docs/` showing the two-step onboarding (script, then migrate).

Out of scope: Terraform (E10), SSO/SAML, creating advisors.

## Acceptance criteria
- [ ] Given a fake `tenant_mgt` client (unit test `tests/scripts/test_provision_idp_tenant.py`), when the script runs twice with the same display name, then `create_tenant` is called once and both runs print the same id.
- [ ] Given a display name that does not exist, then `create_tenant` is called with `allow_password_sign_up=True` and the printed id equals the id the client returned; stdout contains exactly one line.
- [ ] Given the client raises an authorisation or billing error, then the script exits non-zero with a message on stderr and prints nothing on stdout.
- [ ] Given a real project (manual check recorded in the PR description with the output id redacted), then `migrate --onboard-tenant` accepts the printed id and `fa_tenant_lookup(p_idp_tenant_id => <id>)` resolves it.
