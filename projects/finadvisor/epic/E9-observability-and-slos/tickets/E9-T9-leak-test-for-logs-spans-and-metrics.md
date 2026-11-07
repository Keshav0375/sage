---
key: "E9-T9"
title: "Leak test for logs, spans and metrics"
epic: "E9"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E9-T3", "E9-T4", "E9-T6", "E4-T25"]
arch_refs: ["deep-dive/09-observability.md#9.1", "deep-dive/09-observability.md#9.3", "ADR-018"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 229, "id": 6263637287, "url": "https://github.com/Keshav0375/FinAdvisor/issues/229"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
A test fails if any log line, span, metric label or trace contains a request body, SQL parameter or unredacted PII after a full turn.

## Description
Implements the Done-when item: "no log line, span or trace contains request bodies, SQL parameters or unredacted PII (test)". E4-T25 already tests that PII does not reach Voyage, Anthropic, logs or Langfuse; this ticket covers the E9 additions (spans, metric labels, consumer spans) and keeps one canary approach: do not repeat E4-T25's cases, reuse its canary fixtures.
Add backend/tests/observability/test_no_leaks.py (integration, local compose with Postgres and Kafka): run a chat turn with canary message text 'CANARY-BODY-7731 jane.doe@example.com 123-45-6789', an ACL change and an eval-sampled event; capture stdout log lines, all spans from an in-memory exporter (including attributes, events and links), and all metric data points and labels; assert none contains the canary strings or the SQL parameter values bound in that run.
Out of scope: Langfuse payloads (E0-T8, E4-T25).

## Acceptance criteria
- [ ] Given the canary turn, When all logs, spans and metric labels are searched, Then zero matches for 'CANARY-BODY-7731', 'jane.doe@example.com' and '123-45-6789' (pytest test_no_leaks.py fails otherwise).
- [ ] Given OTEL_DB_CAPTURE_PARAMS=true is set by the test, When the same run happens, Then the test fails, proving it can detect parameter capture.
- [ ] Given a deliberately injected logger.info(body=canary) via a test-only hook, When the redactor is bypassed, Then the test fails (negative control).
- [ ] Given the full suite in CI, When it runs, Then this test is included in the required checks.
