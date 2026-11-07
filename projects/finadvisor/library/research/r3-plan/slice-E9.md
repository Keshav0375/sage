# Slice E9

## Epic section (from arch/plan.md)

### E9 Observability and SLOs

- **Goal.** One trace and a few numbers explain any slow or failed request.
- **Scope.**
  - OpenTelemetry end to end (Kong to API to workers, `traceparent` in Kafka headers), log-based metrics (TTFT, gate refusals, guard blocks, consumer lag, rerank fallbacks, degraded-turn ratio, ACL apply lag), dashboards.
  - Availability SLO (prod profile) and latency SLOs; burn-rate and budget alerts; `/readyz` completeness.
- **Arch sections.** overview.md#9, overview.md#6.1 (`/readyz`); ADR-018.
- **Dependencies.** E2, E3, E4, E5, E6.
- **Spikes first.** none.
- **Done when.**
  - A single trace spans Kong, chat-api, a DB query and an LLM call, and a Kafka event's consumer span links to its producer span.
  - Every metric in overview.md#9.2 is emitted and appears on a dashboard; no log line, span or trace contains request bodies, SQL parameters or unredacted PII (test).
  - Each alert in overview.md#9.5 fires in a drill (degraded turns > 5% in 15 min, rerank 429, outbox age, ACL applier lag, DEFAULT partition non-empty, readiness failure, budget).
  - Fixes G-40, G-41, G-44, G-15.

## Arch files to read (paths; read only the named subsections)

- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md  (sections: 6.1)
- context/projects/finadvisor/arch/overview/09-observability.md  (sections: 9)
- context/projects/finadvisor/arch/stack.md (versions)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md §6.6 (config keys), only the keys this epic uses

## ADRs (context/projects/finadvisor/arch/decisions.md; line of heading)

- line 134: ADR-018: Observability and Langfuse Cloud
