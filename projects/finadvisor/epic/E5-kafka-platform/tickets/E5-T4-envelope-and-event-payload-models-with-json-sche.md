---
key: "E5-T4"
title: "Envelope and event payload models with JSON Schema"
epic: "E5"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T14"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.4", "decision-logs.md#adr-013", "deep-dive/11-tech-stack.md"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 81, "id": 6155666025, "url": "https://github.com/Keshav0375/FinAdvisor/issues/81"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Define the common envelope and the catalogue's event payloads as Pydantic models that export JSON Schema, with no text fields on audit and sample events.

## Description
Create the module `events` (backend/src/events/). Envelope per deep-dive/06-interfaces-and-contracts.md#6.4: `{event_id, event_type, schema_version, tenant_id, occurred_at, trace_context, payload}`. One payload model per event type: DocBronzeLanded, DocSilverReady, ChunksContextualized, ChunksIndexed, PublicIngestStage, AclChangeRequested, AclChangeApplied, AdvisorEntitlementChanged, TurnCompleted, TurnRefused, EscalationCreated, TurnUsage, TurnSampled, FeedbackRecorded, JudgeScored, EvalRunCompleted, with the fields in the catalogue row only. A registry maps event_type -> (topic, model, schema_version). Payload models forbid extra fields (`extra='forbid'`).

Round 4 amendments (ADR-013 amended 2026-11-07, R4-D19 M5, ADR-029). Quote 6.4: `chat.audit.v1` events carry '{ids, hashes, retrieved chunk ids, scores, flags (model, gate result, retrieval_degraded); no text}' and `eval.sample.v1` carries 'message_id, chunk ids, hashes, flags; no text'. So TurnCompleted, TurnRefused, EscalationCreated and TurnSampled have NO answer, question, excerpt or redacted-text field; text stays in Postgres `messages`. `AdvisorEntitlementChanged` carries `pseudonym_id` (not `advisor_id`), as in the 6.4 catalogue. Subject-bearing payloads carry ids, hashes, scores, flags and `pseudonym_id` only. `DocBronzeLanded` carries the catalogue fields including `source`, `source_class`, `licence_class`, `valid_from`. A shared name list `FORBIDDEN_TEXT_FIELDS` (raw_content, raw_text, prompt, question, answer, excerpt, text, redacted_question, redacted_answer) is exported for the sink and outbox-writer checks. Where the catalogue gives a free-form list, define typed fields and list the invented ones in the PR. Export `json_schema(event_type)`. Out of scope: registration (E5-T5), Kafka I/O, the outbox writer (E4-T21).

## Acceptance criteria
- [ ] Given a valid envelope dict for each of the 16 event types, when parsed, then it validates (parametrised unit test over all types).
- [ ] Given an envelope with an unknown payload field, when parsed, then validation fails (extra forbidden).
- [ ] Given every payload model, when its fields are listed, then none is named in FORBIDDEN_TEXT_FIELDS, and TurnCompleted, TurnRefused, EscalationCreated and TurnSampled have no free-text `str` field beyond ids, enums and hashes (unit test test_payloads_carry_no_text scanning model_fields).
- [ ] Given AdvisorEntitlementChanged, when its fields are read, then it has `pseudonym_id` and no `advisor_id` (unit test).
- [ ] Given the event-type registry, when each entry is looked up, then its topic matches the 6.4 catalogue (test with the catalogue encoded as a fixture) and `json_schema()` returns a dict with `$schema` for every type.
