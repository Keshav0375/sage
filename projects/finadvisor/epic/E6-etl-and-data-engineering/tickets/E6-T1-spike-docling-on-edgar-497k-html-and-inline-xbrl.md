---
key: "E6-T1"
title: "Spike: Docling on EDGAR 497K HTML and inline XBRL"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T21"]
arch_refs: ["deep-dive/04-1-key-flows.md#4.14", "deep-dive/04-components-and-responsibilities.md#4.7", "decision-logs.md#adr-014"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 142, "id": 6263493380, "url": "https://github.com/Keshav0375/FinAdvisor/issues/142"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Measure Docling parse quality and Voyage token sizes on 497K filings and record the result as an ADR.

## Description
Arch (deep-dive/04-1-key-flows.md §4.14, Flow 2 notes): 'Docling on 497K and inline-XBRL tables is a spike (section 10).' Plan E6: 'Spikes first. Docling on the 497K HTML and inline-XBRL tables (chunk sizes measured with Voyage count_tokens).' Take a sample of at least 30 real EDGAR 497K filings (include some with inline-XBRL tables), parse each with Docling, chunk structure-aware (children 256-512 tokens, parents ~1k tokens per 4.7), and count tokens with the Voyage `count_tokens` API (EMBED_MODEL voyage-4). Measure per filing: parse seconds, peak memory, table fidelity (rows/cols preserved, hand-checked on 5), and the distribution (p50/p95/max) of child and parent token counts. Decide whether Docling is usable in-process in `etl-public` and what fallback is needed for tables (the arch names Document AI only as an OCR fallback). Write the result to `docs/adr/docling-497k.md` in the FinAdvisor repo with the measurements, the sample list (accession numbers), the decision and the pinned Docling version. The researcher copies it into decision-logs.md later. Out of scope: building the pipeline; fetching more than the sample (respect SEC access rules, declared User-Agent, rate limit under 10 req/s).

## Acceptance criteria
- [ ] `docs/adr/docling-497k.md` exists and contains a table of >=30 filings with parse time, peak memory and child/parent token p50/p95/max
- [ ] The ADR states a keep/change decision for Docling and lists the pinned version; `grep -c 'Decision' docs/adr/docling-497k.md` >= 1
- [ ] Child chunk token p95 is reported against the 512 limit and parent p95 against ~1k; any filing type exceeding them is listed
- [ ] Spike script is committed under `backend/scripts/spikes/` and reruns with one command documented in the ADR
