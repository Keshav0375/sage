# sentinel: path to production

> Part of [architecture](architecture.md) · [state](state.md) · [ADRs](decision-logs.md)

**Status: a roadmap, not built.** The MVP (built as Phase 2) is a single-service, single-owner portfolio
system that has never run live end to end ([state](state.md)). This file lists what a team adopting
it would still need. Nothing below exists today; none of it is decided in an ADR yet. Where a row names
a current limit, that limit is taken from [architecture](architecture.md) and the deep-dive files.

## Stages

| Stage | What it is | Status |
|---|---|---|
| POC (proof of concept) | local demo: synthetic JSON scenarios, SQLite memory, backend-executed remediation via an approval tool, no auth ([00](deep-dive/00-poc-and-the-pivot-to-mvp.md)) | replaced |
| MVP (built as Phase 2) | real scenario branches + Datadog, the revert PR as the human gate, GHA executes, Postgres + pgvector + Redis + checkpoints, AKS scale-to-zero, Entra auth, eval, ops dashboard | built, not yet run live |
| Production | the gaps below | not built |

## Gaps

### Onboarding and scale

| Area | Today (MVP) | Needed for production |
|---|---|---|
| Multi-service and multi-tenant | one seeded service (`sentinel-watchtower`) in the `services` table | a services registry that teams self-register into; real monitors per service; per-tenant isolation of memory, runbooks and the revert-PR target repo |
| High availability | one backend replica, scaled to zero between runs; single Postgres and Redis; one pending incident at a time (concurrency group) | multi-replica backend on an AKS user node pool, Postgres HA, Redis HA, a queue in place of the single-pending concurrency group |
| Cost guardrails | free-grant infra, LLM about $5-12/month, owner watches it | budgets and alerts per subscription and per tenant; a hard LLM spend cap |

### Security and access

| Area | Today (MVP) | Needed for production |
|---|---|---|
| Network and TLS | backend endpoint is plain `http` on a load-balancer IP | private networking, a TLS-terminating ingress with a real certificate |
| Secret rotation | fine-grained PATs (including `REVERT_PR_PAT`) with 90-day expiries, rotated by hand | a GitHub App with short-lived installation tokens; automated rotation and expiry alerts |
| Dashboard access | public, observe-only, on GitHub Pages | SSO and RBAC in front of the dashboard |
| Policy and approvals | any reviewer can merge a revert PR | CODEOWNERS on revert PRs, required reviewers per service tier, change windows |

### Operations and governance

| Area | Today (MVP) | Needed for production |
|---|---|---|
| Observability of Sentinel itself | Langfuse traces, Datadog signal for the target app | SLOs and alerting on Sentinel (time to diagnosis, failed runs, queue depth, cold-start time) |
| Data retention and PII | R14 keeps raw tool and log data out of external stores; no retention policy | retention periods for Postgres, Langfuse and logs; a PII review of what reaches traces |
| Disaster recovery | fail-closed pre-destroy backup and a data-only restore, never exercised against Azure | scheduled backups, restore drills with a recovery-time target |
| Model governance | an offline eval and an in-cluster eval Job, not yet run live | eval gates in CI before any prompt or model change; model and prompt version pinning with rollback |
| Evidence | offline tests only | a live end-to-end run and a live eval baseline to compare against |

## Suggested order

1. Live end-to-end run and eval baseline (it makes every other row measurable).
2. TLS and private networking, GitHub App, dashboard SSO: the exposure and secret items.
3. CODEOWNERS and change windows, spend cap, SLOs and alerts.
4. Services registry and multi-tenancy, then HA and queueing.
5. Retention, DR drills and eval gates in CI.
