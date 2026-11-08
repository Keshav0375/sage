---
key: "E6-T8"
title: "New workflow — Sentinel — Pause / Resume"
epic: "E6"
repo: "Sentinel-infra"
size: "S"
status: "done"
depends_on: ["E5-T2"]
arch_refs: ["deep-dive/09-infra-terraform.md#9.4", "deep-dive/09-infra-terraform.md#9.6"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 37, "id": 5694993633, "url": "https://github.com/Keshav0375/sentinel-brain/issues/37"}
branch: "dev/infra-phase-6-dynamic-deployments"
pr: "https://github.com/Keshav0375/Sentinel-infra/pull/8"
updated: "2026-11-08"
---

## Summary
New file `ci_pause.yml`. Stops everything that bills compute, without deleting anything.

## Description
Source: infra task 6.8 (`sentinel-brain/implementation/tasks/infra/phase-6-dynamic-deployments/task-8-pause-resume-workflow.md`).

Runs as **`gha-ops`** on `environment: ops` — the custom start/stop role. Pause is the most
frequently run operation here and must not require the identity that can delete the
subscription.

| Resource | Paused how | Cost while paused |
|---|---|---|
| AKS | `az aks stop` — nodes deallocated | compute **stops**; OS disks remain |
| Postgres (shared + dedicated) | `az postgres flexible-server stop` | compute **stops**; storage remains |
| App Service | `az webapp stop` | F1 is free regardless |
| Functions | Consumption — already zero idle | — |
| namespace workloads | scale to 0 replicas | — |
| **ACR** | **cannot pause** | flat daily charge; covered by the free grant |
| **AKS load balancer** | **cannot pause** | persists while the cluster exists |

**Pause is not zero cost, and the workflow must say so.** It prints what it stopped *and what it
could not*, because a pause button that implies zero spend is worse than no button.

**Two limits that will surprise anyone who does not read this:**
- **Postgres auto-restarts after 7 days.** Azure forces it; there is no opt-out. A pause is a 7-day lease. An optional `schedule:` trigger re-pauses nightly and no-ops when already stopped.

## Acceptance criteria
- [ ] pause → every listed resource stopped; resume → all running
- [ ] Idempotent both ways: pausing a paused estate is a no-op, not an error (`az ... stop` on a stopped server *errors*, so state must be checked first)
- [ ] Runs under `gha-ops` and **fails** if attempted with a create or delete action — verify the role is genuinely narrow
- [ ] Summary lists what was stopped, what was skipped, and what cannot be paused
- [ ] Dedicated databases discovered dynamically, not hardcoded

## Outcome
Shipped but never executed: `ci_pause.yml` has zero runs, so `gha-ops`, the `ops` environment and its custom start/stop role have never authenticated. The category gate was signed with this recorded. Proving it needs a live estate: apply platform, pause, resume, destroy (about 50 minutes).
