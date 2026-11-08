---
key: "E12-T3"
title: "Spike: Langfuse trace delete behaviour against a stub"
epic: "E12"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: []
arch_refs: ["decision-logs.md#adr-30", "decision-logs.md#adr-29", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#24"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 307, "id": 6263804421, "url": "https://github.com/Keshav0375/FinAdvisor/issues/307"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Pin down the Langfuse batch-delete request, response and failure shapes the erasure step must handle, and build the stub used by test #24.

## Description
ADR-030: Langfuse deletion is 'usually within 15 minutes' with no confirmation (evidence-r4.md 2.3); ADR-029: batch delete by trace id, retry, alert at 24 h. Read the Langfuse public API docs for trace deletion (single and batch by ids) and run it once against the Langfuse Cloud project used in E0 with a throwaway trace: record the status code, whether a follow-up GET returns 404 immediately, and the time to disappearance. Build `tests/stubs/langfuse_stub.py` (an in-process HTTP stub) with three modes: `honour` (202 then removed), `ignore` (202, trace stays forever, the #24 case) and `error` (500 then 202). Output `docs/adr/langfuse-delete-behaviour.md`. Out of scope: the erasure step itself.

## Acceptance criteria
- [ ] Given the stub in `ignore` mode, when a client issues a batch delete and then GETs the trace, then the stub returns 202 and the trace is still present (unit test of the stub).
- [ ] Given `error` mode, the first delete call returns 500 and the second 202 (unit test).
- [ ] `docs/adr/langfuse-delete-behaviour.md` records the real request shape, response codes and the measured seconds until a deleted trace stops being returned, from one real run.
