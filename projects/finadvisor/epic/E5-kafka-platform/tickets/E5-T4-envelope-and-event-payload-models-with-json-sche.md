---
key: "E5-T4"
title: "Envelope and event payload models with JSON Schema export"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T14"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.4", "decision-logs.md#adr-013", "deep-dive/11-tech-stack.md"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 81, "id": 6155666025, "url": "https://github.com/Keshav0375/FinAdvisor/issues/81"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Define the common envelope and the catalogue's event payloads as Pydantic models that export JSON Schema.

## Description
Create the module `events` (backend/src/events/). Envelope per deep-dive/06-interfaces-and-contracts.md#6.4: `{event_id, event_type, schema_version, tenant_id, occurred_at, trace_context, payload}`. One payload model per event type: DocBronzeLanded, DocSilverReady, ChunksContextualized, ChunksIndexed, PublicIngestStage, AclChangeRequested, AclChangeApplied, AdvisorEntitlementChanged, TurnCompleted, TurnRefused, EscalationCreated, TurnUsage, TurnSampled, FeedbackRecorded, JudgeScored, EvalRunCompleted, with the fields listed in the catalogue row (only the fields named there; where the catalogue gives a free-form list such as 'ids, hashes, redacted text', define typed fields and list the ones invented in `questions`). A registry mapping event_type -> (topic, model, schema_version). Payload models forbid extra fields (`extra='forbid'`) and have no field for raw document text or raw prompts (payload minimisation, D13j). Export function `json_schema(event_type)` used later for Schema Registry. Out of scope: registration (E5-T5), Kafka I/O.

## Acceptance criteria
- [ ] Given a valid envelope dict for each of the 16 event types, when parsed, then it validates (parametrised unit test over all types).
- [ ] Given an envelope with an unknown payload field, when parsed, then validation fails (extra forbidden).
- [ ] Given every payload model, when its fields are listed, then none is named raw_content, prompt or raw_text (unit test scanning model_fields).
- [ ] Given the event-type registry, when each entry is looked up, then its topic matches the deep-dive/06-interfaces-and-contracts.md#6.4 catalogue (unit test with the catalogue encoded as a fixture) and `json_schema()` returns a dict with `$schema` for every type.
