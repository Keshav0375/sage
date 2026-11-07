---
key: "E3-T1"
title: "Spike: Voyage rerank latency, TPM and tier"
epic: "E3"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E0-T14"]
arch_refs: ["deep-dive/02-quality-attributes.md#2.1", "deep-dive/06-interfaces-and-contracts.md#6.6", "decision-logs.md#adr-008"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 61, "id": 6155642852, "url": "https://github.com/Keshav0375/FinAdvisor/issues/61"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Measure rerank-2.5-lite and rerank-2.5 latency and rate limits on the Voyage tier in use and record the result as an ADR.

## Description
Build a throwaway-but-committed script `backend/scripts/spike_rerank.py` (not imported by the app) that calls Voyage rerank with realistic payloads and records the result as an ADR in `docs/adr/ADR-E3-01-rerank-latency-tpm.md` in the FinAdvisor repo (the orchestrator copies it to arch/decision-logs.md).

Arch being tested (ADR-008): "Voyage `rerank-2.5-lite` (or `rerank-2.5`) with timeout ... rerank p95 < 700 ms ... rerank is single-vendor (Voyage) and rate limited (about 5 QPS on Tier 1)"; deep-dive/02-quality-attributes.md §2.1: "Rerank | p95 < 700 ms | Voyage rerank ~0.68 s per call measured by a third party on short facts". Config §6.6: "`RERANK_TIMEOUT_MS`, `RERANK_CANDIDATES`, `RERANK_TOP_N` | timeout: set in E3; candidates: default 15, range 10-30; top-n 6".

Measure, for both models: (a) latency p50/p95/p99 over >= 200 calls for candidate counts 10, 15, 20, 30 with 256-512-token child chunks (use synthetic finance-style text) and a short query; (b) sustained load at 1, 3 and 5 QPS for 60 s each and the number of HTTP 429 responses and their Retry-After / error body shape; (c) the account's tier and TPM/RPM limits as read from the Voyage dashboard or response headers, with the date. Output a table in the ADR: model x candidates x p50/p95/p99, and QPS x 429 count.

The ADR must state: the chosen `RERANK_MODEL`, the chosen `RERANK_TIMEOUT_MS` (this is the value E3 sets), whether p95 < 700 ms holds at `RERANK_CANDIDATES` 15, the highest QPS without 429, and the exact exception/status Voyage raises on 429 and on timeout (needed by the rerank ticket E3-T6). If p95 >= 700 ms at 15 candidates the ADR must say so and name the fallback (smaller candidate count or dropping rerank).

Out of scope: the app integration (E3-T6), the recall ablation (E7 and E3-T16), any change to production code. Needs `VOYAGE_API_KEY` in the environment; the script must exit 2 with a clear message when it is missing and must never print the key.

## Acceptance criteria
- [ ] Given VOYAGE_API_KEY is unset when `python backend/scripts/spike_rerank.py` runs then it exits with code 2 and prints no key material (checked by `backend/tests/test_spike_scripts.py::test_spike_rerank_requires_key`).
- [ ] Given a valid key when the script runs with `--calls 200` then it writes `docs/adr/ADR-E3-01-rerank-latency-tpm.md` containing a measured p50, p95 and p99 in ms for each of rerank-2.5-lite and rerank-2.5 at candidate counts 10, 15, 20 and 30 (file exists and the table has 8 rows).
- [ ] The ADR records 429 counts at 1, 3 and 5 QPS (60 s each), the Voyage tier and TPM/RPM limits with the measurement date, and the exception type or HTTP status seen on 429 and on client timeout.
- [ ] The ADR states a numeric `RERANK_TIMEOUT_MS`, the chosen `RERANK_MODEL`, and an explicit yes/no for 'p95 < 700 ms at 15 candidates' that matches the measured table.
