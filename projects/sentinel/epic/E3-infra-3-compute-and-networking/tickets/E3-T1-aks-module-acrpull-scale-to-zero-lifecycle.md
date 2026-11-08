---
key: "E3-T1"
title: "AKS module (+ AcrPull, scale-to-zero lifecycle)"
epic: "E3"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E2-T1", "E1-T3"]
arch_refs: ["deep-dive/09-1-identity-plane.md#9.11"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 11, "id": 5694989578, "url": "https://github.com/Keshav0375/sentinel-brain/issues/11"}
branch: "dev/infra-phase-3-compute-modules"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/3"
updated: "2026-11-08"
---

## Summary
Single-node AKS that hosts the backend. Node pool idles at 0; workflows scale it — so

## Description
Source: infra task 3.1 (`sentinel-brain/implementation/tasks/infra/phase-3-compute-modules/task-1-aks-module.md`).

Terraform must NOT fight `node_count`.

**Files created:** `modules/aks/{main.tf,variables.tf,outputs.tf}`
- `azurerm_kubernetes_cluster "sentinel"` — name `sentinel-aks`, dns_prefix `sentinel`, `sku_tier = "Free"`, default_node_pool `default` node_count 1 vm_size `Standard_B2ats_v2`, `identity { type = "SystemAssigned" }`.
- `lifecycle { ignore_changes = [default_node_pool[0].node_count] }` — the scale-to-zero rule.
- `azurerm_role_assignment "aks_acr_pull"` — `AcrPull` to `kubelet_identity[0].object_id` scoped to the ACR id (input).
- `azurerm_role_assignment "gha_aks_user"` — `Azure Kubernetes Service Cluster User Role` to the GHA SP object id.
- `variables.tf` — `resource_group_name`, `location`, `acr_id`, `gha_principal_id`.
- `outputs.tf` — `aks_cluster_name`, `aks_resource_group`.

## Acceptance criteria
- [x] Validates; `ignore_changes` on node_count present (else applies fight scale-to-zero).
- [x] AcrPull + Cluster User role assignments wired to the right principals.
- [x] Outputs expose cluster name + RG.

## Outcome
_not yet implemented_
