---
key: "E5-T2"
title: "Three CI identities + GitHub environments"
epic: "E5"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E5-T0"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.3", "deep-dive/09-1-identity-plane.md#9.9"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 25, "id": 5694991784, "url": "https://github.com/Keshav0375/sentinel-brain/issues/25"}
branch: "dev/infra-phase-5-dynamic-foundations"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/7"
updated: "2026-11-08"
---

## Summary
Dynamic deployments create their own resource groups, and destroy must purge Key Vaults. Neither

## Description
Source: infra task 5.2 (`sentinel-brain/implementation/tasks/infra/phase-5-dynamic-foundations/task-2-three-identities.md`).

is possible with rights scoped to one resource group, so the CI identity gains **subscription
scope** — which supersedes R5's scoping and R6's refusal to let CI tear down.

R5's *intent* survives: the dangerous rights must be unreachable from a pull request. That is
achieved by splitting the identity, not by narrowing the scope.

| Identity | Rights | Federated subjects | Reachable from a PR? |
|---|---|---|---|
| `gha-plan` | **Reader** (subscription) + Storage Blob Data Contributor (state) | `:pull_request`, `:environment:plan` | yes — and it can change nothing |
| `gha-deploy` | **Contributor** + **RBAC Administrator** + Key Vault purge + **AKS RBAC Cluster Admin** (subscription) | `:environment:production`, `:environment:destroy` | **no** |
| `gha-ops` | custom role: `*/start/action`, `*/stop/action`, `*/read` only | `:environment:ops` | **no** |

**Why the environment subject is the mechanism, not a policy.** A job declaring `environment: X`
receives the OIDC subject `repo:<owner>/<repo>:environment:X` instead of the branch form. GitHub
will not mint that token for a `pull_request` event. So `gha-deploy` is unreachable from a PR
**by construction** — there is no rule to misconfigure. This is the same behaviour that failed
the first phase-4 apply, used deliberately.

**`gha-ops` gets a custom role rather than Contributor** because pause/resume is the operation
run most often and should carry the least privilege. Contributor can delete; a start/stop role

## Acceptance criteria
- [x] Three UAMIs exist; `gha-plan` has **no** write action anywhere (verified by a failing test apply)
- [x] Custom role JSON contains only read + start/stop actions and no `Microsoft.Authorization/*`
- [x] Every environment subject has a matching FIC in **both** tenants (the phase-4 lesson: the two-tenant split doubles the credential surface)
- [x] `bootstrap-identities.sh` is idempotent — second run is a no-op
- [x] Imported into state; `terraform plan` → no changes

## Outcome
_not yet implemented_
