---
key: "E4-T6"
title: "LLMClient: circuit breaker and eval-gated same-provider fallback"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T5"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#ADR-005"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 98, "id": 6155684888, "url": "https://github.com/Keshav0375/FinAdvisor/issues/98"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Add a circuit breaker and a fallback to LLM_MODEL_FALLBACK only when LLM_FALLBACK_ENABLED is true.

## Description
Extend LLMClient. Breaker params from LLM_BREAKER_* (failure threshold, window, open duration, half-open probes); when open, calls fail fast with LLM_UNAVAILABLE. Fallback: after primary exhausts retries or the breaker is open, if and only if LLM_FALLBACK_ENABLED is true, retry once on LLM_MODEL_FALLBACK (claude-sonnet-4-6; same provider only, never another vendor); the usage record carries the model actually used. Fallback has its own prompt cache and 1,024-token minimum (use spike result). Config default false until the eval gate passes (E7). Quote ADR-005: 'same-provider fallback only ... enabled only if it passes the eval gate'.

## Acceptance criteria
- [ ] Given primary forced to fail and LLM_FALLBACK_ENABLED=false, when streaming, then LLM_UNAVAILABLE is raised and the fallback model is never called (test).
- [ ] Given primary forced to fail and LLM_FALLBACK_ENABLED=true, when streaming, then the fallback model is used and usage.model equals LLM_MODEL_FALLBACK; no temperature/top_p/top_k sent.
- [ ] Given N consecutive failures, when the breaker opens, then the next call fails without a network request until the open duration passes (fake clock test); half-open success closes it.
