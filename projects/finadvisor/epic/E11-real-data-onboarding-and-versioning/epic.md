---
key: "E11"
title: "Real data onboarding and versioning"
phase: 3
phase_name: "Real data and lifecycle"
repo: "FinAdvisor"
status: "todo"
depends_on: ["E3", "E4", "E6"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.15 to #4.18", "deep-dive/04-2-source-lifecycle-and-cells.md#4.25", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.9", "deep-dive/06-interfaces-and-contracts.md#6.7", "deep-dive/06-interfaces-and-contracts.md#6.8", "deep-dive/06-interfaces-and-contracts.md#6.10", "decision-logs.md#adr-026", "decision-logs.md#adr-027", "decision-logs.md#adr-028", "decision-logs.md#adr-034", "decision-logs.md#adr-036", "decision-logs.md#adr-038"]
issue: null
updated: "2026-11-07"
---

## Goal
The first real corpus (US, EU and UK law plus private demo publisher documents) enters through one connector framework with change capture, version history, contracts and licences, and "as of" questions are answered from versions.

## Scope
Tickets E11-T1 to E11-T27 (spikes T1-T3 first).
- Connector framework (T6-T8): `list`, `changes`, `fetch`, `classify`; `source_registry` and append-only `source_observations`; 48 h overlap; silent edit; two-strike withdrawal; mass-delete breaker; empty listing is a failure. Tables: T4, T5.
- Bitemporal versions (T5, T9): `document_versions` with EXCLUDE, `reconcile_lineage`.
- Connectors: `ecfr` T15, `sec` 497K T16 and RR facts T17, `eurlex` T18, `legislation_gov_uk` T19, `fca_api` T20, `publisher` T21, optional ESMA T27.
- Source classes and `fund_rr_facts` (T10); contracts and quarantine (T11, T12); Model Armor document screening (T13); egress rule (T14); FCA kill switch and `purge_source` (T22).
- As-of and cache (T23, T24); poison corpus (T25); first corpus, fixtures and weekly smoke (T26).

## ADRs
ADR-026, ADR-027, ADR-028, ADR-034, ADR-036, ADR-038 (and the ADR-039 amendments).

## Exit criteria
- Versions v3, v1, v2 in all permutations give an identical valid-time line; A-B-A representable (#11, #8).
- A listing of 0 items or a 30% drop applies nothing, freezes the connector and pages (#12); silent edit gives a new system-range row, alert, reproducible with `known_at` (#13).
- Poison corpus never indexed, consumers continue (#5); `EXECUTION_SKIPPED` quarantines.
- A new version of a cached PUBLIC document misses the cache and returns the new text (#3).
- FCA question as of 2019 refused with "no version history for this source" (#25); `purge_source('fca_api')` empties PUBLIC stores, bumps `source_epoch`, writes `source_purges`.
- Private ingest with `llm_egress_ack=false` refused with zero provider calls (#26).
- Retire-vs-erase policy test per source class; over 5% quarantined pauses the connector; every connector passes its fixture suite and the weekly live smoke runs; parser bump and replay leaves no old-parse chunk.
