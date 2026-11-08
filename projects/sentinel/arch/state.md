# sentinel: arch state

## Decided
- ADR-001 to ADR-019 (2026-06-30 to 2026-07-12): planning rounds for Phase 2: three repos, agentic
  loops, backend reasons / GHA executes, the PR as the human gate, Postgres + pgvector, Langfuse,
  AKS scale-to-zero, OIDC, Entra bearer, Azure-native secrets, the 30 scenario branches.
- ADR-020 to ADR-029 (2026-07-26 to 2026-08-30): control plane split, identity plane on managed
  identities, two tenants, infra cost and lifecycle, ARM64 AKS, Terraform-only infra CI, the dynamic
  multi-deployment platform, deferred LLM federation.
- ADR-030 to ADR-041 (2026-10-04 to 2026-10-25): per-phase build contracts for deployment and backend.
- ADR-042 to ADR-045 (2026-10-25 to 2026-10-28): release and monorepo, ops dashboard, memory hardening,
  in-cluster eval.
- Source: `sentinel-brain/architecture/decisions.md` (binding there; this file set is a port).

## Validated
- Every phase passed an `architecture-warden` conformance review (CONFORMS) before sign-off, plus
  code review (LGTM) and, for backend and identity phases, a safety review (SAFE).
- Proven live: the infra identity plane (OIDC from CI, RBAC, state), the full infra lifecycle from an
  empty subscription (apply platform and deployment, destroy, verify 11/11), Entra-token Postgres
  login, the deploy pipeline (one live run green except the then-missing table).
- Proven offline only: the whole backend (fake LLM, stubbed Langfuse), scenario catalog and offline
  e2e, dashboard (e2e 18/18, Lighthouse), memory hardening and the eval Job.

## Open
- Nothing in the architecture is undecided. Open items are live verification and owner steps:
  [deep-dive/15-open-questions.md](deep-dive/15-open-questions.md) and [../state.md](../state.md).
- Known drift in the source docs: some prose in `backend.md` and `infra.md` predates phases 5-11
  (for example `sentinel-rg`, node-pool scaling, `dummy-api-0375`); the decision log and the shipped
  code win, and this port follows them.
