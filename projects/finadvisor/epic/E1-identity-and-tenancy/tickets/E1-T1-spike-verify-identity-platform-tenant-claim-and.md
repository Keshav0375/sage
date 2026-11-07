---
key: "E1-T1"
title: "Spike: verify Identity Platform tenant claim and billing"
epic: "E1"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T14"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/08-security-and-privacy.md#8.2", "decision-logs.md#adr-010"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 17, "id": 6155588477, "url": "https://github.com/Keshav0375/FinAdvisor/issues/17"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
The exact ID-token tenant claim, firebase-admin tenant-aware verification behaviour and the >2-tenant billing rule are confirmed against a real Identity Platform project and recorded as an ADR.

## Description
Spike, first ticket of E1 (D14.17). Arch text to confirm: "the `firebase.tenant` claim names the IdP tenant, and `tenant_mgt.auth_for_tenant(tenant_id).verify_id_token(...)` checks signature, `aud`, `iss`, `exp` and raises `TenantIdMismatchError` on a tenant mismatch" (deep-dive/04-components-and-responsibilities.md §4.5 `auth`; 8.2 step 4: "The claim name is verified in the first E1 ticket"). Also 8.2 step 7: "Identity Platform multi-tenancy needs billing enabled for more than 2 tenants; email/password tier free to 50k MAU".

Build a throwaway probe script `backend/scripts/spikes/idp_claim_probe.py` (not imported by app code). With a real GCP project that has Identity Platform and multi-tenancy enabled (project id from `IDP_PROJECT_ID`, credentials via ADC):
1. Create 3 IdP tenants (more than 2, to observe the billing requirement), enable email/password on each, create one user per tenant, sign in through the REST sign-in endpoint with the tenant id and obtain an ID token.
2. Decode each token (no verification) and record the exact JSON path of the tenant claim, plus `sub`, `aud`, `iss`.
3. Verify with `firebase_admin.tenant_mgt.auth_for_tenant(<tenant>).verify_id_token`: (a) token of tenant A against tenant A (ok), (b) token of tenant B against tenant A (expect `TenantIdMismatchError`), (c) an expired token, (d) a token with a different project audience. Record the exception class raised for each.
4. Record whether creating the 3rd tenant is rejected without billing and succeeds with billing (operator action: the project owner enables billing; note the date).
5. Add `firebase-admin` to the lockfile (pinned; deep-dive/11-tech-stack.md says "pin at implementation") and record the version.

Record the result as `docs/adr/idp-multitenancy-claim.md` in this repo (the researcher copies it into `arch/decision-logs.md` as the next ADR number after merge; do not write to the harness repo) with: the claim path, the exceptions per case, the billing observation, the pinned firebase-admin version, whether the Firebase Auth emulator supports multi-tenancy (if yes, E1-T13 and CI use the emulator; if no, locally signed test JWTs with a test JWKS), and which one is chosen for E1-T13.

Out of scope: any production auth code (E1-T13), Terraform, SSO.

## Acceptance criteria
- [ ] Given a token issued by IdP tenant B, when `idp_claim_probe.py --check` verifies it with `auth_for_tenant(A)`, then it raises `TenantIdMismatchError`; the script exits non-zero if any of cases (a)-(d) behaves differently from the ADR's recorded outcome.
- [ ] The ADR file `docs/adr/idp-multitenancy-claim.md` exists and names the exact claim JSON path found in a real decoded token (matching the claims printed by the probe and saved in `docs/adr/idp-probe-output.json`, which contains no secrets or raw tokens).
- [ ] The ADR records, for 3 tenants in one project, whether the 3rd tenant creation succeeded and under which billing state, with the date.
- [ ] `poetry.lock` contains a pinned `firebase-admin` version and the ADR states the same version (`poetry show firebase-admin` equals the ADR value).
- [ ] The ADR states whether the Auth emulator supports multi-tenancy and names the single approach E1-T13 uses (emulator, else locally signed JWTs with a test JWKS).
