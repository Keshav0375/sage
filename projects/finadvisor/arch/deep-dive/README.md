# finadvisor: deep-dive index

> Back to [architecture](../architecture.md) · [diagram](../architecture-diagram.md) · [ADRs](../decision-logs.md) · [state](../state.md)

One component or concern per file. Binding; agents read by section.

- [00-as-built-baseline.md](00-as-built-baseline.md): the MVP as built at d6c2bd3, diagrams, data model, gap register (62 gaps).
- [01-context-and-goals.md](01-context-and-goals.md): goal, Keshav's decisions, non-goals, MVP gaps and where v2 fixes them.
- [02-quality-attributes.md](02-quality-attributes.md): latency, availability, scale, quality gates, cost, erasure promise, as-of, reconciliation, eval sizes.
- [03-system-context-and-boundaries.md](03-system-context-and-boundaries.md): system context diagram, trust and egress boundaries, source systems.
- [04-components-and-responsibilities.md](04-components-and-responsibilities.md): containers diagram and each component 4.1-4.13.
- [04-1-key-flows.md](04-1-key-flows.md): sequence diagrams of chat, ingest and the other critical flows (4.14).
- [04-2-source-lifecycle-and-cells.md](04-2-source-lifecycle-and-cells.md): connectors, versioning, indexer, erasure, ACL applier, cells, guardrail gates (4.15-4.27).
- [05-data-model-and-storage.md](05-data-model-and-storage.md): ER diagram, tables, roles.
- [05-1-rls-indexes-versioning-and-deletion.md](05-1-rls-indexes-versioning-and-deletion.md): RLS, indexes, hybrid SQL, cache, versions, deletion tables, retention (5.4-5.14).
- [06-interfaces-and-contracts.md](06-interfaces-and-contracts.md): HTTP API, SSE, tools, Kafka topics, Kong, config keys, connector, deletion API, cells directory.
- [07-scaling-failure-modes-and-recovery.md](07-scaling-failure-modes-and-recovery.md): failure modes, scale triggers, recovery, edge cases, provider limits, regional cells and tenant move.
- [08-security-and-privacy.md](08-security-and-privacy.md): OWASP mapping, authentication, network, secrets, leak paths, ingest scan, egress and erasure, role policy.
- [09-observability.md](09-observability.md): traces, metrics, logs, health, SLOs, reconciliation alerts, deletion receipts, guardrail measurement.
- [10-open-questions.md](10-open-questions.md): spikes and unverified facts.
- [11-tech-stack.md](11-tech-stack.md): stack table with versions (target and as built).
