> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
## 1. Context and goals

### 1.1 Problem

When a deploy breaks a service, the first 30 minutes of incident response are mechanical: notice
the alert, find the deploy that caused it, read the logs, decide between rolling back and calling
a human, and write it up. Sentinel automates that triage and diagnosis with a multi-agent pipeline,
but stops short of acting: it drafts a revert pull request (or an escalation) and a human decides.

The hard part is not the agents; it is trust. An agent system is only credible if:
- it is tested against **real failures with known answers**, not against data written next to the
  expected output;
- it **cannot act on the world by itself**;
- every credential is short-lived and scoped, and nothing secret sits in a pod or a repo;
- its reasoning is traced, scored by a judge that is not itself, and replayable.

### 1.2 Motivation and goals

Sentinel is Keshav's portfolio system for agentic DevOps: three code repos driven by one control
plane, built phase by phase by Claude Code agents under human sign-off.

1. **Real ground truth.** A real FastAPI app on Azure App Service, genuinely deployed and watched by
   Datadog, with 30 scenario branches whose expected outcome is labelled in a catalog. The same
   catalog is the eval set ([08](08-deployment-and-scenarios.md)).
2. **Human in the loop by construction.** The backend reasons; GitHub Actions executes; the revert
   PR is the only gate ([10](10-security-and-hitl.md)).
3. **No stored cloud secrets.** OIDC for CI, Entra bearer for the API, workload identity for the
   pod, Entra-only Postgres ([09-1](09-1-identity-plane.md)).
4. **Agentic patterns that self-correct.** Plan-execute, reflexion and reverification, with caps
   enforced in code ([04](04-agent-pipeline.md)).
5. **Near-zero idle cost.** Everything on free grants; the cluster stopped between runs; LLM calls are
   the only real spend ([13](13-cost.md)).
6. **Everything reproducible.** Terraform for the estate; one workflow input creates or destroys a
   whole isolated deployment ([09](09-infra-terraform.md)).

### 1.3 Owner constraints (binding)

- Owner: Keshav, sole author. No AI attribution in any commit, PR or merge.
- Azure for Students subscription inside a university tenant: Owner on the subscription, **no
  directory write rights**, and no institutional involvement. This forced the two-tenant identity
  split ([ADR-022](../decision-logs.md#adr-022)).
- Region `canadacentral` (R3); regional quota 6 vCPU; every small AKS SKU allowed there is ARM64.
- GitHub owner `Keshav0375`, exact repo casing (OIDC `sub` claims are case-sensitive).
- Budget: LLM calls only, about $5-12/month; Redis B0 (about $13/month) accepted later.
- Architecture is law: a task that disagrees with the architecture halts and asks.

### 1.4 Non-goals

- Sentinel never merges, deploys, reverts or approves anything.
- No PR-lifecycle tracking (fire-and-forget: the job ends when the revert PR exists).
- No load-driven or probabilistic fault scenarios (F1 cannot express them deterministically).
- No multi-replica backend; a few incidents a day, one at a time.
- Production hardening beyond a dev estate (public LB IP, Postgres firewall open in dev).
