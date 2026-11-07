---
key: "E10-T2"
title: "Spike: worker pool scale to 0 and Terraform support"
epic: "E10"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E0-T14"]
arch_refs: ["ADR-019", "ADR-020", "deep-dive/04-components-and-responsibilities.md#4.12"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Verify a Cloud Run worker pool can be set to 0 instances and managed by Terraform with ignore_changes, as an ADR.

## Description
ADR-019 and ADR-020 list 'worker pool scale to 0 and its Terraform support' as unverified. Verify with a minimal worker pool using the chosen Google provider version from deep-dive/11-tech-stack.md.

Build: a throwaway Terraform config under scripts/spikes/worker_pool/ that creates a Cloud Run worker pool (google_cloud_run_v2_worker_pool) from a hello-world image with manual_instance_count = 1 and lifecycle.ignore_changes = [scaling[0].manual_instance_count] (check the real attribute path), then: (a) set count to 0 with `gcloud run worker-pools update --scaling` or the documented equivalent and confirm 0 instances run and no billing for idle; (b) run `terraform plan` and confirm no diff; (c) scale back to 2 and plan again; (d) record the exact gcloud command the demo scripts must use.

Output: docs/adr/worker-pool-scale-to-zero.md with commands, provider version, plan outputs, and the result. If scale to 0 or the Terraform resource is not supported, the ADR states the fallback (for example min instance count semantics or deleting/recreating the pool) and that the fallback must be raised as a question before E10-T9.
Out of scope: the real fa-worker pool (E10-T9).

## Acceptance criteria
- [ ] docs/adr/worker-pool-scale-to-zero.md records the provider version and the exact gcloud command that sets instance count to 0 and to N
- [ ] After scaling to 0 `gcloud run worker-pools describe` shows instance count 0, and `terraform plan -detailed-exitcode` returns exit code 0 (no drift) with ignore_changes set; both outputs are in the ADR
- [ ] After scaling to 2 `terraform plan -detailed-exitcode` still returns 0
- [ ] The throwaway worker pool and its Terraform state are destroyed; `gcloud run worker-pools list` is empty
