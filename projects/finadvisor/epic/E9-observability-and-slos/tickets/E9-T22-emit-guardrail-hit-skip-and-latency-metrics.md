---
key: "E9-T22"
title: "Emit guardrail hit, skip, latency and numeric-gate metrics"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T5", "E4-T9", "E4-T11", "E4-T12", "E4-T19"]
arch_refs: ["deep-dive/09-observability.md#9.9", "deep-dive/09-observability.md#9.2", "deep-dive/02-quality-attributes.md#2.1", "decision-logs.md#adr-036", "decision-logs.md#adr-037"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 221, "id": 6263620424, "url": "https://github.com/Keshav0375/FinAdvisor/issues/221"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Every guardrail records hits, skips and latency on the live path so the 150 ms rule and the weekly precision and recall can be read in one place.

## Description
Implements 9.9: "Precision, recall and latency per guardrail are measured weekly on the eval sets of 2.10 ... and exported as the gauges of 9.2, with live counters for hits, skips and latency. Rule: a guard whose p95 adds more than 150 ms to the critical path moves to async-after-first-sentence or is dropped. Numeric-gate false rejects on correct answers are tracked against the proposed 3% line. Model Armor latency is measured from the Cloud Run region before its timeout is fixed."

Add a small helper `observe_guard(guard)` (context manager) in backend/src/observability/ that times a guard call and records `guard_latency_ms{guard}` through `metrics.record` (E9-T5), and apply it to each guard on the chat path: the input cap, Presidio pseudonymization (E4-T8), the Model Armor input screen (E4-T9), the sentence-buffered output redaction (E4-T12), the citation verifier (E4-T11) and the numeric grounding gate. Record:
- `guard_hits_total{guard,reason}` whenever a guard blocks, redacts or withholds (reason from a fixed per-guard list);
- `guard_skipped_total` for each Model Armor `EXECUTION_SKIPPED` (the input screen fails open with an audit flag, ADR-036; the counter is how that is watched);
- `numeric_gate_reject_total{reason}` for each answer the numeric gate withholds;
- the existing `guard_blocks_total{guard}` and `citation_rejected_total` stay where E4 emits them; this ticket removes no emitter and a grep test asserts each of the new names is recorded in exactly one module.
`guard_precision{guard}` and `guard_recall{guard}` are weekly gauges written by the eval runs of E7-T25 and E7-T26, not by this code. Labels carry no text, ids or tenant data. Out of scope: the guard logic, dashboards (E9-T12), the eval sets (E7).

## Acceptance criteria
- [ ] Given a guard stub that sleeps 40 ms with a fake clock, When wrapped by observe_guard('presidio'), Then `guard_latency_ms{guard='presidio'}` is recorded once with 40 (test `test_guard_metrics.py::test_latency_recorded`).
- [ ] Given a Model Armor client stub returning EXECUTION_SKIPPED, When the input screen runs, Then `guard_skipped_total` increments by 1, the turn is not blocked and the audit flag is set (test `test_guard_metrics.py::test_execution_skipped_counted`).
- [ ] Given an answer with an ungrounded figure, When the numeric gate withholds it, Then `numeric_gate_reject_total{reason='numeric_ungrounded'}` increments by 1 and the refusal reason is the same string.
- [ ] Given a guard hit with reason 'x' outside the guard's fixed reason list, When recorded, Then it raises (test `test_guard_metrics.py::test_reason_list_fixed`).
- [ ] A grep test asserts `guard_hits_total`, `guard_skipped_total`, `guard_latency_ms` and `numeric_gate_reject_total` are each recorded in exactly one module, and that no label value is longer than 64 characters.
