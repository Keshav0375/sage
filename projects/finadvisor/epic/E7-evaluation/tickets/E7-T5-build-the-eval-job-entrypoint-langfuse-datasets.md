---
key: "E7-T5"
title: "Build the eval job entrypoint, Langfuse datasets and run record"
epic: "E7"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T21", "E5-T14", "E7-T2"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/06-interfaces-and-contracts.md#6.4", "deep-dive/06-interfaces-and-contracts.md#6.6", "ADR-017"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Provide a `jobs eval` entrypoint that runs as fa_eval against the eval tenant, syncs the golden set to Langfuse and emits EvalRunCompleted.

## Description
Add the `eval` Cloud Run job entrypoint on the existing `jobs` image entrypoint (arch 4.8: `eval` | `fa_eval` | "Full or subset eval run (L1-L3) against the dedicated `eval` tenant; results to Langfuse and `eval.events.v1`"). Arguments: `--subset pr|full`, `--layers l1,l2,l3`, `--model answer|fallback`. It opens DB connections as `fa_eval` only (role created in E1), pinned to `EVAL_TENANT_ID`; it must refuse to start if EVAL_TENANT_ID is unset or if the connected role is not fa_eval. It syncs the golden set to a Langfuse dataset (`run_experiment`), writes a JSON result file (metrics, git sha, model ids, prompt version) and produces `EvalRunCompleted` on `eval.events.v1` with the `eval` service-account Kafka key using an idempotent producer (event_id derived from run id). The ~60-question PR subset is selected by a `subset: pr` flag on cases (stratified, set in this ticket for existing cases). Out of scope: metric computation (T6, T8, T10), CI wiring (T12).

## Acceptance criteria
- [ ] Given DB user fa_app, the entrypoint exits non-zero with a message naming the role mismatch (unit test).
- [ ] Given EVAL_TENANT_ID unset, the entrypoint exits non-zero before any DB or LLM call (unit test).
- [ ] `--subset pr` selects between 55 and 65 cases and every category is represented (unit test on the shipped golden set once T3 is merged).
- [ ] Integration test with the CI Kafka container: a dry run produces exactly one EvalRunCompleted message; running it twice with the same run id yields one logical event (dedupe on event_id).
