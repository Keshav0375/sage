---
key: "E10-T13"
title: "Terraform Identity Platform tenant provisioning"
epic: "E10"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E10-T4"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.13", "deep-dive/04-components-and-responsibilities.md#4.8", "ADR-010", "ADR-012"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 234, "id": 6263642102, "url": "https://github.com/Keshav0375/FinAdvisor/issues/234"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Provision Identity Platform and one IdP tenant per firm from Terraform with email/password sign-in.

## Description
4.13 and 4.12: Identity Platform multi-tenancy, one IdP tenant per firm, billing enabled for > 2 tenants, email/password free to 50k MAU; deep-dive/04-components-and-responsibilities.md §4.8 migrate row: 'the IdP tenant itself is provisioned by an onboarding script in E1 and Terraform in E10'. ADR-010 (tenant-aware verification, IDP_PROJECT_ID used for aud/iss).

Build terraform/identity.tf: google_identity_platform_config with multi_tenant { allow_tenants = true }, authorized domains for the ALB host, and google_identity_platform_tenant for each entry in a variable `idp_tenants` (map slug -> display name; at minimum the demo firms and the eval tenant slug) with allow_password_signup = true. Output the tenant IDs as a map so the migrate job `--onboard-tenant <slug>` mapping can read them (do not change the E1 script). Do not create users.

Out of scope: the E1 onboarding script, the SPA sign-in UI (E8).

## Acceptance criteria
- [ ] `terraform plan` creates one google_identity_platform_tenant per entry of idp_tenants (terraform test with a 3-entry map expects 3 resources)
- [ ] `gcloud identity-platform tenants list` (or the REST list) shows each tenant with email/password sign-in enabled after apply; output attached
- [ ] The output `idp_tenant_ids` maps every slug to a tenant ID and `terraform output -json` contains no secret values
