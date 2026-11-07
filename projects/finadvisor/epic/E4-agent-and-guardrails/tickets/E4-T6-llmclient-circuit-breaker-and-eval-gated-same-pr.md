---
key: "E4-T6"
title: "LLMClient: breaker, fallback gating, model-retirement guard"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T5"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#adr-005", "decision-logs.md#adr-039", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 98, "id": 6155684888, "url": "https://github.com/Keshav0375/FinAdvisor/issues/98"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add a circuit breaker, a fallback only when LLM_FALLBACK_ENABLED is true, and a test that a retired model fails mid-stream into LLM_UNAVAILABLE.

## Description
Extend LLMClient. Breaker params from LLM_BREAKER_* (failure threshold, window, open duration, half-open probes); when open, calls fail fast with LLM_UNAVAILABLE. Fallback: after primary exhausts retries or the breaker is open, if and only if LLM_FALLBACK_ENABLED is true, retry once on LLM_MODEL_FALLBACK (claude-sonnet-4-6; same provider only); usage carries the model actually used. Config default false until the eval gate passes (E7). ADR-005: 'same-provider fallback only ... enabled only if it passes the eval gate'. No temperature, top_p or top_k is ever sent (removed in API version 2026-10-21).

Round 4 model-retirement guard (edge case #10, tiers PR and W; 04 §4.5: 'CI and readiness fail on a retired or soon-retiring model'): a fake provider that returns 404 (model not found) mid-stream makes the client emit the normalised error `LLM_UNAVAILABLE` (SSE `error {LLM_UNAVAILABLE}`), count it as a breaker failure so the breaker opens after the threshold, and use the fallback only when the flag is on. Add a readiness check function `check_models_available()` that calls the model list endpoint (stubbed in tests) and fails when LLM_MODEL_ANSWER or LLM_MODEL_AUX is missing from it; the CI job runs it with the stub. Out of scope: the eval gate (E7).

## Acceptance criteria
- [ ] Given primary forced to fail and LLM_FALLBACK_ENABLED=false, when streaming, then LLM_UNAVAILABLE is raised and the fallback model is never called (test).
- [ ] Given primary forced to fail and LLM_FALLBACK_ENABLED=true, when streaming, then the fallback model is used and usage.model equals LLM_MODEL_FALLBACK; captured bodies contain no temperature/top_p/top_k.
- [ ] Given a fake provider returning 404 after the first streamed chunk (#10), when the turn streams, then the error is LLM_UNAVAILABLE, the breaker records a failure, and after N such calls the next call fails without a network request (fake clock); with the flag off the fallback is not called, with it on the fallback is called (test_model_retirement_mid_stream).
- [ ] Given the model-list stub missing LLM_MODEL_ANSWER, when `check_models_available()` runs, then it raises and the readiness probe reports not ready (test).
- [ ] Given N consecutive failures, when the breaker opens, then the next call fails without a network request until the open duration passes; half-open success closes it (fake clock).
