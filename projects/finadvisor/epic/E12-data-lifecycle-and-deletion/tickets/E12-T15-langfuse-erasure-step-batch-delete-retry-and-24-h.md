---
key: "E12-T15"
title: "Langfuse erasure step: batch delete, retry and 24 h alert"
epic: "E12"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E12-T8", "E12-T3"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "decision-logs.md#adr-30", "decision-logs.md#adr-29", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4#24"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 292, "id": 6263768409, "url": "https://github.com/Keshav0375/FinAdvisor/issues/292"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Delete traces by trace id with retry, and alert at 24 h when the delete is not honoured.

## Description
StoreStep `langfuse`: collect `messages.trace_id` for the scope (persisted by E12-T10 before the messages are deleted), call the batch delete found in E12-T3 in batches, then verify with GETs on the next run. Not honoured (still returned after the call) -> retry with backoff each worker pass; at 24 h from the first call emit `erasure_langfuse_unconfirmed` and set an alert (metric via the E9 module; the Terraform policy is E9), and the receipt stays phase 1 (6.9: Langfuse not honouring a delete: retry, alert at 24 h, receipt stays phase 1). Window kind `provider`, text 'provider best effort'. Out of scope: Terraform alert policy.

## Acceptance criteria
- [ ] Given the stub in `ignore` mode (E12-T3), when the step runs for 24 h of fake clock, then the retry count is greater than 1, the `erasure_langfuse_unconfirmed` metric fires once, and the receipt stays phase 1 (#24).
- [ ] Given `honour` mode, when the step runs, then a follow-up GET returns 404 and the step is `done` with `window_kind = provider`.
- [ ] Given `error` mode, then the step retries and succeeds on the second call without failing the request.
- [ ] Given a trace id of another tenant in the batch, then it is never sent (the id list comes only from the request's own messages).
