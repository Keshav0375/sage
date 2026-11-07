---
key: "E4-T1"
title: "Spike: Model Armor latency from Cloud Run region, fallback rates"
epic: "E4"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E1-T21"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#adr-009", "decision-logs.md#adr-036", "decision-logs.md#adr-039"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 93, "id": 6155679177, "url": "https://github.com/Keshav0375/FinAdvisor/issues/93"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Measure Model Armor sanitizeUserPrompt latency from the Cloud Run region and set the timeout, the flag default and the 150 ms rule from the numbers.

## Description
Spike (E4 'Spikes first'). Round 4 (ADR-036 amended, ADR-039 V3, R4-D18 V3): Model Armor GA status, SLA and latency are NOT published, so the fixed '500 ms, fail closed' is replaced: the timeout is set from latency measured from the Cloud Run region, the feature is behind a flag (`MODEL_ARMOR_ENABLED`), and 'a guard adding more than 150 ms p95 on the critical path moves async or is dropped'. Call the Model Armor regional endpoint (template = MODEL_ARMOR_TEMPLATE) from a Cloud Run-like environment in the cell's region with 200 redacted prompts of 50-2000 chars (benign, injection, jailbreak). Record p50/p95/p99 latency, the added critical-path latency when run in parallel with the Voyage embed (serial cost = max(0, armor - embed)), false-positive rate on the benign set, detection rate on the injection set, and the rate of timeouts at candidate timeouts. Compare with the in-process fallback (Presidio plus heuristic injection patterns) on the same set. Output: an ADR addendum under ADR-009 with the numbers and decisions: `MODEL_ARMOR_TIMEOUT_MS`, whether `MODEL_ARMOR_ENABLED` defaults true or false, and whether the guard stays synchronous (<= 150 ms p95 added) or moves async or is dropped. Out of scope: the production client (E4-T9).

## Acceptance criteria
- [ ] Given 200 prompts, when the benchmark script runs from the Cloud Run region (or the closest available environment, stated), then p50, p95, p99, added critical-path latency, false-positive and detection rates are written to the ADR addendum.
- [ ] Given the measured added p95, when it exceeds 150 ms, then the ADR states async or drop as the decision; when at or below, it states the timeout in ms derived from p99 and the resulting timeout rate as a percentage.
- [ ] Given the fallback comparison, when read, then the ADR lists detection and false-positive rates of Presidio plus heuristics on the same set and states the audit-flag rate expected when Model Armor times out (fail open).
- [ ] The benchmark script is committed, re-runnable with one command, and exits non-zero if the template or endpoint is unreachable.
