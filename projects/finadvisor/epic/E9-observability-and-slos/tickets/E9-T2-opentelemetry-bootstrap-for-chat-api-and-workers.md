---
key: "E9-T2"
title: "OpenTelemetry bootstrap for chat-api and workers"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T3", "E9-T1"]
arch_refs: ["deep-dive/09-observability.md#9.1", "ADR-018", "deep-dive/11-tech-stack.md (Telemetry)"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 218, "id": 6263617761, "url": "https://github.com/Keshav0375/FinAdvisor/issues/218"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
One shared init function configures OTel tracing with FastAPI, asyncpg and HTTP client instrumentation, SQL parameter capture off, exporting to the OTLP endpoint.

## Description
Implements deep-dive/09-observability.md §9.1: "OpenTelemetry end to end: Kong opentelemetry (traceparent) to chat-api (FastAPI, asyncpg / SQLAlchemy, Voyage and Anthropic HTTP calls) to workers ... to Cloud Trace. SQL parameter capture off; no request bodies in spans (D13o)." Stack: OpenTelemetry SDK + exporters, versions pinned at implementation (deep-dive/11-tech-stack.md).
Build backend/src/observability/tracing.py (exists; rework) with init_tracing(service_name) used by the chat-api app factory and by the worker/job entrypoints:
- TracerProvider with resource service.name, deployment.environment = ENV_PROFILE; OTLP exporter to OTEL_EXPORTER_OTLP_ENDPOINT (config key, required); BatchSpanProcessor.
- W3C traceparent propagation; FastAPI instrumentation continues the traceparent Kong sends.
- asyncpg / SQLAlchemy instrumentation with parameter capture controlled only by OTEL_DB_CAPTURE_PARAMS (default false; the db.statement attribute is replaced by the operation and table, no literals).
- httpx/aiohttp instrumentation for Voyage and Anthropic calls with request/response body and header capture disabled.
- A SpanProcessor that deletes any attribute whose key is in the E9-T1 denylist or that is longer than 256 characters.
- init is a no-op when the endpoint is unset in dev profile.
Out of scope: span names in the turn pipeline (E9-T3), worker spans (E9-T4), the Kong plugin (E2-T15).
Export path (resolution R77): direct OTLP to the Google Cloud Telemetry API endpoint (telemetry.googleapis.com) authenticated with Application Default Credentials; no sidecar. FIRST step of this ticket is a verification: send a test span from a Cloud Run service (or a scratch project with ADC) and confirm it appears in Cloud Trace. Write the outcome to docs/adr/otel-export.md. If direct export fails, the fallback is an OTel Collector sidecar on Cloud Run; record that decision, the evidence and the changed deployment in the same ADR before building it. OTEL_EXPORTER_OTLP_ENDPOINT is set accordingly.

## Acceptance criteria
- [ ] Given OTEL_DB_CAPTURE_PARAMS=false, When a query 'SELECT * FROM advisors WHERE email = $1' runs with a parameter 'a@b.com' under an in-memory exporter, Then no exported span attribute value contains 'a@b.com' (pytest test_tracing_sql.py).
- [ ] Given a request with a traceparent header, When it hits GET /healthz, Then the exported server span has the same trace_id and its parent_span_id equals the header's span id.
- [ ] Given an httpx call to a stubbed api.anthropic.com with a JSON body containing 'SECRETPROMPT', When exported, Then no span attribute contains 'SECRETPROMPT'.
- [ ] Given an attribute named 'body' or a 300-char value is set on a span, When the span ends, Then the exported span lacks it.
- [ ] Given the verification run, When a span is exported with ADC to the Telemetry API endpoint, Then it is returned by the Cloud Trace API (gcloud/REST get trace) within 60 s, and docs/adr/otel-export.md exists with the result and the fallback decision (CI file-presence check fails if the ADR is missing).
