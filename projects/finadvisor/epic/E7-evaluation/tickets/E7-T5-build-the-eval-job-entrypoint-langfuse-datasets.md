---
key: "E7-T5"
title: "Build the eval job entrypoint, Langfuse datasets and run record"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T21", "E5-T14", "E7-T2"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/06-interfaces-and-contracts.md#6.4", "deep-dive/06-interfaces-and-contracts.md#6.6", "deep-dive/02-quality-attributes.md#2.10", "decision-logs.md#adr-017", "decision-logs.md#adr-037"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 185, "id": 6263556931, "url": "https://github.com/Keshav0375/FinAdvisor/issues/185"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Provide a `jobs eval` entrypoint that runs as fa_eval against the eval tenant, selects the PR subset, aborts at EVAL_BUDGET_USD, syncs the golden set to Langfuse and emits EvalRunCompleted.

## Description
Add the `eval` Cloud Run job entrypoint on the existing `jobs` image entrypoint (arch 4.8: `eval` | `fa_eval` | "Full or subset eval run (L1-L3) against the dedicated `eval` tenant; results to Langfuse and `eval.events.v1`; ablation runs use the Message Batches API (ADR-037)"). Arguments: `--subset pr|full`, `--layers l1,l2,l3`, `--model answer|fallback`. It opens DB connections as `fa_eval` only (role created in E1), pinned to `EVAL_TENANT_ID`; it refuses to start if EVAL_TENANT_ID is unset or the connected role is not fa_eval.

R4 changes:
- `--subset pr` selects the tranche-1 items (the 60-item PR subset of deep-dive/02 2.10; for the `synthetic` split before the real set exists, the flagged synthetic subset). Private items are skipped when the private bucket is not mounted and the skipped count is written to the result file (K-R4-3).
- `EVAL_BUDGET_USD` is a required setting (06 6.6: "required; caps eval runs; value set in E7"). The run keeps a running cost from token usage and a price table in config and aborts the run, non-zero, with the partial result file marked `aborted_budget: true` when the next call would pass the cap (Done when: a run aborts at `EVAL_BUDGET_USD`).
- The result file also records the golden-set hash, the number of clusters present, and the skipped private count.

It syncs the golden set to a Langfuse dataset (`run_experiment`), writes a JSON result file (metrics, git sha, model ids, prompt version), and produces `EvalRunCompleted` on `eval.events.v1` with the `eval` service-account Kafka key using an idempotent producer (event_id derived from run id). Out of scope: metric computation (E7-T6, E7-T8, E7-T10), CI wiring (E7-T11), the ablation runner (E7-T7).

## Acceptance criteria
- [ ] Given DB user fa_app, the entrypoint exits non-zero with a message naming the role mismatch (unit test).
- [ ] Given EVAL_TENANT_ID or EVAL_BUDGET_USD unset, the entrypoint exits non-zero before any DB or LLM call (unit tests).
- [ ] Given a stub LLM whose calls cost $0.40 each and EVAL_BUDGET_USD=1.00, when a run starts, then it makes exactly 2 calls, exits non-zero, and the result file has `aborted_budget: true` (test `test_eval_budget.py::test_run_aborts_at_budget`).
- [ ] `--subset pr` selects exactly the tranche-1 items of the shipped file, every category represented; with the private bucket unset the private items are absent and `skipped_private` equals their count (unit test).
- [ ] Integration test with the CI Kafka container: a dry run produces exactly one EvalRunCompleted message; running it twice with the same run id yields one logical event (dedupe on event_id).
