---
key: "E5-T3"
title: "Platform layer — shared ACR, AKS, Postgres"
epic: "E5"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E5-T1", "E5-T2"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.3", "deep-dive/09-1-identity-plane.md#9.9"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 26, "id": 5694991925, "url": "https://github.com/Keshav0375/sentinel-brain/issues/26"}
branch: "dev/infra-phase-5-dynamic-foundations"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/7"
updated: "2026-11-08"
---

## Summary
The resources every deployment shares, in their own resource group and their own Terraform

## Description
Source: infra task 5.3 (`sentinel-brain/implementation/tasks/infra/phase-5-dynamic-foundations/task-3-platform-layer.md`).

workspace.

**Why one cluster.** The subscription's regional quota is **6 vCPU** and an AKS node is 2. A
cluster per deployment stops at three, with no headroom. A namespace per deployment scales to
whatever the cluster's RAM holds. The isolation is not weaker for being logical: workload
identity federates on `system:serviceaccount:<namespace>:<sa>`, so a pod in one namespace cannot
mint a token for another's Key Vault. That is enforced by the token exchange, not by naming.

**AKS:** `oidc_issuer_enabled`, `workload_identity_enabled`, one `Standard_B2pls_v2` ARM64 node,
`ignore_changes` on node_count. Backend images must therefore build `linux/arm64` — unchanged
from phase 3.

**Postgres:** one flexible server, Entra-only auth, pgvector. Deployments in `mode: shared` get
a database and an Entra role here; `mode: dedicated` builds its own server in its own RG (task
6.3).

**Separate workspace is not a preference, it is a safety property.** In one state,
`terraform destroy` of a deployment would take the cluster with it. Separate states make that
structurally impossible.

## Acceptance criteria
- [x] `terraform workspace list` → `platform` exists and is selected for these resources
- [x] AKS OIDC issuer URL is a root output (deployments consume it)
- [x] ACR is Standard (the free grant covers 1 Standard registry — Basic is a different, billable meter)
- [x] Outputs published for every value a deployment needs: cluster name, OIDC issuer, ACR login server, PG FQDN, PG admin
- [x] Nothing here references a deployment name

## Outcome
_not yet implemented_
