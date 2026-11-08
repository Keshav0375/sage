---
key: "E6-T2"
title: "Kubernetes namespace + per-namespace workload identity"
epic: "E6"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E6-T1"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.4", "deep-dive/09-infra-terraform.md#9.6"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 31, "id": 5694992704, "url": "https://github.com/Keshav0375/sentinel-brain/issues/31"}
branch: "dev/infra-phase-6-dynamic-deployments"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/8"
updated: "2026-11-08"
---

## Summary
The deployment's slice of the shared cluster. Adds provider `hashicorp/kubernetes ~> 2.0`,

## Description
Source: infra task 6.2 (`sentinel-brain/implementation/tasks/infra/phase-6-dynamic-deployments/task-2-namespace-and-identity.md`).

authenticated from the AKS admin credential in the platform remote state.

**The isolation argument, precisely.** The federated credential subject is
`system:serviceaccount:<d>-<env>:sentinel-backend`. Different namespace → different subject →
different UAMI → different Key Vault and database grants. A pod in `t2-dev` presenting its token
cannot obtain `t1-dev`'s vault access, because Entra matches the subject string exactly and
there is no wildcard form. This is cryptographic separation, not a convention.

**A `ResourceQuota` is not optional here.** With one shared cluster, an unbounded namespace can
exhaust the node and take every other deployment down with it. The quota is what makes "shared
cluster" acceptable rather than merely cheap.

## Acceptance criteria
- [x] Namespace, quota, netpolicy and annotated ServiceAccount all created
- [x] The FIC subject contains the namespace; two deployments have provably different subjects
- [x] **Negative test:** a pod in namespace A cannot read namespace B's Key Vault — run it, do not assume it
- [x] Deleting a deployment deletes its namespace and leaves the cluster healthy

## Outcome
_not yet implemented_
