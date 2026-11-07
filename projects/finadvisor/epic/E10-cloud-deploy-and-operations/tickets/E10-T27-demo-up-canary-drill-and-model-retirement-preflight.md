---
key: "E10-T27"
title: "Add the canary drill and model preflight stages to demo-up"
epic: "E10"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E10-T18", "E10-T25", "E12-T21"]
arch_refs: ["deep-dive/09-observability.md#9.8", "deep-dive/04-1-key-flows.md#4.14", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4", "deep-dive/06-interfaces-and-contracts.md#6.6", "decision-logs.md#adr-030", "decision-logs.md#adr-029"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
After the system is ready, `demo-up` runs the canary drill and then a 1-token call per pinned model, and prints both results before the URL.

## Description
Implements the E10 round-4 line: "`demo-up` runs the erasure job first, then the canary drill (synthetic advisor through chat, trace, events and BigQuery, erased, time to zero per observable store), then the retirement preflight (1-token call per pinned model)". The erasure job step is in E10-T18. 9.8: "Canary: `demo-up` runs the erasure job first, then drives a synthetic canary advisor ... It runs at each demo start, not on a weekly cron, because the system is often stopped."

Insert two stages into scripts/demo/demo_up.py between `demo-prewarm` and the final print:
1. Run the `erasure-canary` job (E10-T25, code E12-T21) and wait for it to exit. The drill needs chat-api, Kafka and the pipeline up, so it runs only after `demo-prewarm` has succeeded and never before the erasure job (the order test of E12-T21 holds). The script prints one line per observable store with seconds to zero, or `canary=FAILED store=<s> age=<n>` when the drill reports a store that did not reach zero inside its documented window; a FAILED canary does not stop `demo-up` (the drill itself raises the `canary_failed` alert and triggers the re-sweep, E12-T21, E9-T20) and the script's exit code stays 0 unless the job itself crashed (non-zero exit of the job). Stores with multi-day windows (Kafka, BigQuery) are recorded at a later start; the printout says `pending window` for them.
2. Run a new `model-preflight` Cloud Run job (defined in this ticket's Terraform, no DB role, only the Anthropic and Voyage secrets) that makes a 1-token call with each configured model id: LLM_MODEL_ANSWER, LLM_MODEL_JUDGE, LLM_MODEL_FALLBACK, the contextualizer and condense models, the embed model and the rerank model. A model that errors with a not-found or retired response makes the job exit non-zero and `demo-up` print `model preflight FAILED: <id>` and exit non-zero (the system stays up; the person decides). The 1-token calls are the only LLM spend of this stage.
Out of scope: the canary code (E12-T21), the retirement date metric `model_retirement_days` (E9), a cron for either stage (not wanted).

## Acceptance criteria
- [ ] Unit test with fake clients: the full call order is now sql=ALWAYS, erasure job, valkey create, gateway revision, min instances up, worker up, scheduler resume, maintenance, demo-prewarm, erasure-canary, model-preflight; moving the canary before the erasure job or before demo-prewarm fails the test (`test_demo_up.py::test_canary_after_prewarm_and_erasure`).
- [ ] Unit test: a canary job whose output says `FAILED store=langfuse age=90000` makes `demo-up` print `canary=FAILED store=langfuse` and still run model-preflight; the exit code is 0 (`test_demo_up.py::test_failed_canary_does_not_stop`).
- [ ] Unit test: a canary job process that exits non-zero makes `demo-up` exit non-zero.
- [ ] Unit test with a stub provider that answers one configured model id with a not-found error: the preflight job exits non-zero naming that id and `demo-up` exits non-zero; with all models answering it exits 0.
- [ ] `terraform plan` lists the `model-preflight` job with no DB_* variables and no Scheduler trigger; on the real project after `make demo-up` the output shows one line per store and the preflight result; output attached.
