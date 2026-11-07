---
key: "E12-T4"
title: "Spike: Voyage batch throughput under the 25% RPM cap"
epic: "E12"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E3-T3"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.27", "decision-logs.md#adr-35"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Measure Voyage embedding throughput under a client capped at 25% of the RPM limit and compare it with the 20 min and 200 min ceilings.

## Description
ADR-035 and 4.27: the backfill's Voyage client is capped at 25% of RPM (`EMBED_BACKFILL_RATE_FRACTION` = 0.25) and the times 'about 20 min at 100k chunks and 200 min at 1M' are ceilings, not measurements. Using the E3-T3 Voyage client with a rate semaphore at 0.25 of the account RPM (2,000 RPM per the ADR evidence) embed 5,000 synthetic chunks of typical child size with both the real-time and the batch API (batch is 33% off, 12 h window, up to 100K inputs), record wall time, tokens per minute, 429 count and cost, then extrapolate to 100k and 1M. Output `docs/adr/voyage-backfill-throughput.md`: measured vs ceiling and a go or revise note for the `embed-backfill` design (batch or real-time). Out of scope: the backfill job.

## Acceptance criteria
- [ ] Given 5,000 synthetic chunks and a 0.25 semaphore, when the measurement runs, then the doc records wall seconds, chunks per second and 429 count for both APIs.
- [ ] The doc states extrapolated minutes at 100k and 1M next to the 20 and 200 min ceilings and marks each as measured-extrapolated, not ceiling.
- [ ] Given the semaphore at 0.25, the measured request rate never exceeds 0.25 x RPM over any 60 s window (rate-limiter unit test with a fake clock).
