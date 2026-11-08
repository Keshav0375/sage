---
key: "E4-T20"
title: "escalate_to_compliance persistence and GET /v1/escalations"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T10", "E1-T21"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.3", "deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/08-security-and-privacy.md#8.1"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 126, "id": 6263468998, "url": "https://github.com/Keshav0375/FinAdvisor/issues/126"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Persist escalations with server-side licenses and an outbox event; list endpoint.

## Description
Tool (6.3): input {reason, product_class}; licenses read from Principal/advisors.licenses (never tool args); insert into escalations (E1 table) and an outbox row in one transaction; returns {escalation_id, status:'pending_review'}; client sees tool name+status only (G-18). A turn that calls it is flagged side_effect so it is never written to answer_cache. GET /v1/escalations: compliance_officer sees tenant escalations, others only their own (RLS + role check). Reason text is redacted before persist.

## Acceptance criteria
- [ ] Given a tool call, when executed, then exactly one escalations row and one outbox row exist, in the same transaction (rollback test: failure of the outbox insert leaves no escalation).
- [ ] Given an advisor with licenses X, the stored license snapshot equals advisors.licenses and any 'licenses' argument from the model is rejected by schema validation.
- [ ] Given a non-officer, GET /v1/escalations returns only own rows; officer returns tenant rows; other tenant rows never appear.
- [ ] Given a turn that escalated, the answer cache write is skipped (test).
