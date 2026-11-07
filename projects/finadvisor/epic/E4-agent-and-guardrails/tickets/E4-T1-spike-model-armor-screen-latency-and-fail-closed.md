---
key: "E4-T1"
title: "Spike: Model Armor screen latency and fail-closed"
epic: "E4"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E1-T21"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#ADR-009"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 93, "id": 6155679177, "url": "https://github.com/Keshav0375/FinAdvisor/issues/93"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Measure Model Armor sanitizeUserPrompt latency and record ADR-009 evidence.

## Description
Spike (E4 'Spikes first'). Call Model Armor REST (template = MODEL_ARMOR_TEMPLATE) from a Cloud Run-like environment with 200 redacted prompts of 50-2000 chars (benign, injection, jailbreak). Record p50/p95/p99 latency, false-positive rate on the benign set, detection rate on the injection set, and behaviour at a forced 500 ms timeout. Output: an ADR addendum in projects/finadvisor/arch/decision-logs.md under ADR-009 with the numbers and a keep/change verdict for MODEL_ARMOR_TIMEOUT_MS=500 and fail-closed. Arch: ADR-009 'Model Armor input screen in parallel with embed (500 ms timeout, fail closed)'; 4.5 guardrails. Out of scope: production client (see the Model Armor client ticket).

## Acceptance criteria
- [ ] Given 200 prompts, when the benchmark script runs, then p50, p95, p99 latency and false-positive and detection rates are written to the ADR addendum.
- [ ] Given the 500 ms timeout is applied client-side, when p99 is above 500 ms, then the ADR states the resulting fail-closed rate as a percentage and a decision (keep or change).
- [ ] The benchmark script is committed and re-runnable with one command and exits non-zero if the template is unreachable.
