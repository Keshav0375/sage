---
key: "E9-T1"
title: "Structured JSON logging with redaction processor"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T3"]
arch_refs: ["deep-dive/09-observability.md#9.3", "ADR-018"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Every log line is JSON with the 9.3 field set and passes through a redactor that drops bodies, queries, prompts and exception text.

## Description
Implements deep-dive/09-observability.md §9.3: "Structured JSON to stdout, redacted before writing: ts, severity, trace, request_id, tenant_id, advisor_hash, event, error_code. No request bodies, queries, prompts, tool payloads or exception text for clients."
Extend backend/src/observability/logging.py (structlog already present; it currently binds user_id and renders exception info). Build:
- Processors producing exactly the keys ts, severity, trace (Cloud Trace id from the current OTel span, empty if none), request_id, tenant_id, advisor_hash (sha256 of advisor_id, never the raw id), event, error_code, plus event-specific scalar fields.
- A redaction processor with a denylist of keys (body, query, prompt, message, messages, content, tool_input, tool_output, sql, params, exc_info, exception, traceback, authorization, token) that replaces the value with "[redacted]", and runs the E4 PII scrubber (backend/src/pii) over remaining string values.
- Remove format_exc_info: log error_code and exception class name only.
- bind_request_context takes request_id, tenant_id, advisor_id (hash applied inside).
Out of scope: Kong file-log (E2-T15), Langfuse masking (E0-T8), spans (E9-T2), log-based metric definitions (E9-T11).

## Acceptance criteria
- [ ] Given logger.info('x', body='secret text', query='SELECT 1', error_code='INTERNAL'), When captured by a test sink, Then the JSON has body and query equal to '[redacted]', contains the keys ts, severity, trace, request_id, tenant_id, advisor_hash, event, error_code, and the test fails if any other key carries the secret text (pytest backend/tests/observability/test_logging.py).
- [ ] Given logger.exception inside an except ValueError('card 4111 1111 1111 1111'), When captured, Then the line has no 'traceback' or 'exc_info' key and the string '4111' does not appear anywhere in the line.
- [ ] Given bound advisor_id='adv-123', When a line is logged, Then advisor_hash is a 64-hex sha256 and 'adv-123' does not appear in the line.
- [ ] Given an active OTel span, When a line is logged, Then trace equals the span's trace id in Cloud Trace format projects/<p>/traces/<id>; with no span it is an empty string.
