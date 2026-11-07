# Slice E5

## Epic section (from arch/plan.md)

### E5 Kafka platform

- **Goal.** A tested event backbone that the product can lose without breaking chat.
- **Scope.**
  - Topic catalogue `*.v1`, Schema Registry with JSON Schema generated from Pydantic, producer / consumer framework (idempotent producer, `processed_events` dedupe, retries, DLQ `dlq.v1`, envelope-vs-key and PUBLIC rejection).
  - `outbox-relay` worker reading the E1 `outbox` table; `acl-applier` worker applying `acl_change_requests` (ACL-column UPDATE or delete, `acl_version` bump, `answer_cache` purge); per-service Confluent service accounts, API keys and Kafka ACLs; payload minimisation; traceparent in headers.
  - Local compose broker (`apache/kafka:4.4.0`) and Schema Registry; Confluent Cloud Basic cluster in us-central1 first (registry region).
- **Arch sections.** overview.md#6.4, overview.md#4.7, overview.md#5.2 (`outbox`, `processed_events`, `acl_change_requests`); ADR-013, ADR-022.
- **Dependencies.** E1.
- **Spikes first.** Confirm Confluent Basic idle cost in the console (UNVERIFIED estimate); decide partition counts and retention within 1,500 partitions.
- **Done when.**
  - With the broker stopped, a chat request still succeeds and its audit outbox rows are published after the broker returns, with no loss and no duplicates in the sink (integration test with Kafka service container).
  - Redelivering the same event changes no state (`processed_events`); a poison message and an event whose envelope tenant differs from its key land in `dlq.v1` with a redacted payload and a reason.
  - An ACL-change request is applied end to end: `chunks` ACL columns updated, request `applied`, `acl_version` bumped, `answer_cache` rows citing the document purged, zero embed calls; `acl_apply_lag_s` is emitted.
  - Every topic has a registered schema; a breaking schema change is rejected by the registry in CI; each service has its own API key and ACLs (no shared key).
  - Fixes G-48 (audit path is via logs, not Kafka), part of G-11 (service wiring for events).

## Arch files to read (paths; read only the named subsections)

- context/projects/finadvisor/arch/overview/04-components-and-responsibilities.md  (sections: 4.7)
- context/projects/finadvisor/arch/overview/05-data-model-and-storage.md  (sections: 5.2)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md  (sections: 6.4)
- context/projects/finadvisor/arch/stack.md (versions)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md §6.6 (config keys), only the keys this epic uses

## ADRs (context/projects/finadvisor/arch/decisions.md; line of heading)

- line 241: ADR-013: Kafka on Confluent Cloud Basic, Schema Registry, transactional outbox
- line 47: ADR-022: Asynchronous ACL changes through acl_change_requests and an acl-applier worker
