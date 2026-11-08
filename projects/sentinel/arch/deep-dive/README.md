# sentinel: deep-dive index

> Back to [architecture](../architecture.md) · [diagram](../architecture-diagram.md) · [ADRs](../decision-logs.md) · [state](../state.md)

One component or concern per file. Ported from `sentinel-brain/architecture/` (binding there);
section numbers here are this project's own. Agents read by section.

- [00-poc-and-the-pivot-to-mvp.md](00-poc-and-the-pivot-to-mvp.md): the POC (proof of concept), why it was replaced, what the MVP changed, the migration order.
- [01-context-and-goals.md](01-context-and-goals.md): problem, motivation, goals, owner constraints, non-goals.
- [02-quality-attributes.md](02-quality-attributes.md): cost, cold start, agent caps, reliability, eval and delivery targets.
- [03-system-context-and-boundaries.md](03-system-context-and-boundaries.md): the repos and control plane, the end-to-end flow, trust boundaries, external services.
- [04-agent-pipeline.md](04-agent-pipeline.md): orchestrator, agents, loops, tools, models and fallback, budgets (4.1-4.6).
- [04-1-key-flows.md](04-1-key-flows.md): sequence diagrams: runtime incident, deploy-failure fast path, deploy record, eval (4.7-4.10).
- [05-data-and-memory.md](05-data-and-memory.md): schema, correlation chain, episodic/semantic/short-term memory, memory hardening.
- [06-interfaces-and-contracts.md](06-interfaces-and-contracts.md): HTTP API, webhook and dispatch mapping, rollback spec, composite actions, config.
- [07-backend-hosting-and-ci.md](07-backend-hosting-and-ci.md): image, K8s manifests, scale-to-zero, workflows, branch model.
- [08-deployment-and-scenarios.md](08-deployment-and-scenarios.md): the target app, deploy pipeline, the 30 scenario branches, Datadog monitors.
- [09-infra-terraform.md](09-infra-terraform.md): state, modules, platform and deployment layers, toggles, infra CI, preflight, monorepo.
- [09-1-identity-plane.md](09-1-identity-plane.md): two tenants, CI identities, token model, workload identity, inbound auth, secrets (9.8-9.13).
- [10-security-and-hitl.md](10-security-and-hitl.md): HITL invariant, agentic caps, R14 data rule, least privilege, supply chain, known gaps.
- [11-observability-and-ops-dashboard.md](11-observability-and-ops-dashboard.md): Langfuse, Datadog, the ops ledger and dashboard.
- [12-evaluation.md](12-evaluation.md): judge, runner and dataset, in-cluster eval.
- [13-cost.md](13-cost.md): per-resource cost and lessons.
- [14-tech-stack.md](14-tech-stack.md): stack as built.
- [15-open-questions.md](15-open-questions.md): never-run-live behaviour, owner steps, follow-ups.
