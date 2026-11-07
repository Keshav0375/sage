---
key: "E0-T8"
title: "Replace Langfuse v2 tracing with an SDK 5.x wrapper"
epic: "E0"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T1", "E0-T3", "E0-T6"]
arch_refs: ["decision-logs.md#adr-018", "deep-dive/01-context-and-goals.md#1", "deep-dive/11-tech-stack.md#llm-observability"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 9, "id": 6155578560, "url": "https://github.com/Keshav0375/FinAdvisor/issues/9"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Tracing uses real Langfuse 5.x calls behind one wrapper with export masking and capture off on sensitive spans, and a tracing failure never fails a chat.

## Description
Why: G-15: `backend/src/observability/tracing.py` calls `trace()/generation()/span()` which do not exist in the installed SDK, so chat fails with Langfuse keys set, and tests pass only because Langfuse is a `MagicMock`. ADR-018: "Langfuse Cloud Hobby with Python SDK 5.x behind one wrapper: `@observe` with `capture_input` / `capture_output` off on sensitive spans and `mask_otel_spans` for export masking (the legacy `mask=` does not cover OTel spans)". Use the exact parameter names recorded in `docs/spikes/langfuse-sdk5.md` from E0-T1.

Do:
- Rewrite `backend/src/observability/tracing.py` as the only module importing `langfuse`: `init_tracing(settings) -> Tracer | None` (returns `None` and creates no client when `LANGFUSE_ENABLED=false`), a span helper/decorator `traced(name, *, sensitive=True, tenant_id=None)` (sensitive spans record no input or output; tenant tag optional until E1), a masking function applied through `mask_otel_spans` that scrubs text with the existing `src/pii` redactor in regex mode, `flush()` and `shutdown()`. Prompt fetch (`get_prompt_from_langfuse`) stays, failing soft to the fallback prompt.
- Every call into the SDK is wrapped so an exception is logged (`tracing_error`, no payload) and swallowed.
- Update `backend/src/agent/orchestrator.py` (one trace per turn, one generation per LLM iteration, one span per tool call; tool inputs/outputs and message content are sensitive, so capture off) and `backend/src/main.py` (init in lifespan, shutdown on exit). Remove all Langfuse v2 method usage.
- Rewrite `backend/tests/test_tracing.py` against the real installed SDK (no `MagicMock` of the Langfuse class) using an in-memory OpenTelemetry span exporter.

Out of scope: tenant tagging values (E1), OTel exporters to Cloud Trace (later epic), eval datasets and scores (E7).

## Acceptance criteria
- [ ] Given the real SDK with an in-memory span exporter, when a `traced("x", sensitive=True)` span runs with input containing `ssn 123-45-6789` and output text, then the exported span has no input attribute and no output attribute.
- [ ] Given a non-sensitive span whose input contains `jane@example.com`, the exported span attributes do not contain that string (the masking function ran) (unit test).
- [ ] Given `LANGFUSE_ENABLED=false`, `init_tracing` returns `None`, no `Langfuse` object is constructed and the agent still completes a mocked turn (unit test).
- [ ] Given an exporter or client that raises on every call, a mocked agent turn still yields its normal events and the failure is only logged (unit test); this is the regression for G-15.
- [ ] A test builds `unittest.mock.create_autospec(langfuse.Langfuse, instance=True)` and runs the wrapper against it; it fails if the wrapper calls any method the installed SDK does not have (`trace`, `generation`, `span` as on v2).
- [ ] `grep -rn "import langfuse\|from langfuse" backend/src` matches only `backend/src/observability/tracing.py`; ruff, mypy and pytest pass.
