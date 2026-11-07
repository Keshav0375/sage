# Slice E10

## Epic section (from arch/plan.md)

### E10 Cloud deploy and operations

- **Goal.** The system runs in GCP on demand, costs what the budget says, and is released safely.
- **Scope.**
  - Terraform v2: VPC (Direct VPC egress `private-ranges-only`, Private Google Access, `run.app` private zone), PSC Cloud SQL, Cloud Run services / worker pool / jobs, Secret Manager, per-service SAs, WIF, Artifact Registry, Confluent via provider, IdP tenant provisioning. Terraform does not own the Valkey instance (demo script).
  - Deploy pipeline: `migrate` job, tagged no-traffic revision, smoke test, traffic shift. `make demo-up`, `make demo-down` (exact reverse order, 10-minute drain timeout) and the hourly `demo-ttl` job (`fa_maint`); `maintenance` scheduling (hourly while up, run by `demo-up`); `demo-prewarm` job inside the VPC.
  - Load test with a stub LLM; measured Cloud SQL start time; connection budget check (`max_connections` 400, pool budget <= 300); `prod` profile (HA flag); org policy check `constraints/run.managed.requireInvokerIam`.
- **Arch sections.** overview.md#4.12, overview.md#4.14 (flows 5, 6), overview.md#7, overview.md#2.5, overview.md#8.3 to #8.4; ADR-019, ADR-020, ADR-021, ADR-012, ADR-024.
- **Dependencies.** E2 through E9.
- **Spikes first.** Cloud SQL start time and stopped-instance billing; Cloud Run worker pool scale to 0 and Terraform support; ALB forwarding-rule monthly price; Cloud Armor cost (overview §10).
- **Done when.**
  - `make demo-down` leaves the outbox empty (or logs the forced remainder after 10 minutes), consumer lag 0, worker pool 0, API and Kong min 0, Valkey deleted and Cloud SQL stopped, in that order; `make demo-up` runs the exact reverse, reaches a passing `/readyz` through `demo-prewarm` and prints the measured start time; the `demo-ttl` job brings a forgotten demo down.
  - `terraform plan` is clean (no drift) after a down / up cycle thanks to `ignore_changes`.
  - No `allUsers` binding on any service; the invoker check is disabled only on `fa-gateway`; Cloud SQL has no public IP; no secret value in Terraform state; the sum of pool sizes over max instances is <= 300.
  - A load test with a stub LLM runs at ~10 QPS peak and reports the p95 targets of overview §2.1 (excluding LLM time) against the 10k-chunk synthetic corpus numbers (fail if above).
  - Monthly cost for a demo month read from the billing export is within $100-200 (expected $110-160).
  - Fixes G-02, G-10, G-11, G-12, G-13, G-26, G-27, G-29, G-47, G-50, G-51.

## Arch files to read (paths; read only the named subsections)

- context/projects/finadvisor/arch/overview/02-quality-attributes-with-numbers-load-lat.md  (sections: 2.5)
- context/projects/finadvisor/arch/overview/04-components-and-responsibilities.md  (sections: 4.12, 4.14)
- context/projects/finadvisor/arch/overview/07-scaling-failure-modes-and-recovery.md  (sections: 7)
- context/projects/finadvisor/arch/overview/08-security-and-privacy.md  (sections: 8.3)
- context/projects/finadvisor/arch/stack.md (versions)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md §6.6 (config keys), only the keys this epic uses

## ADRs (context/projects/finadvisor/arch/decisions.md; line of heading)

- line 263: ADR-012: Edge: external ALB + Cloud Armor, same origin
- line 112: ADR-019: Compute mapping: one image, three entrypoints, Cloud Run, Vite SPA
- line 90: ADR-020: Demo-on-demand operations and Cloud SQL sizing
- line 69: ADR-021: CI/CD with GitHub Actions, WIF and a gated deploy
- line 5: ADR-024: VPC egress mode: Direct VPC egress private-ranges-only, no Cloud NAT
