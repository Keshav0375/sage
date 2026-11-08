---
key: "E6-T9"
title: "Suitability-rule extraction, validation and lookup"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T7", "E1-T5", "E3-T11"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/05-data-model-and-storage.md#5.2", "decision-logs.md#adr-014"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 163, "id": 6263522679, "url": "https://github.com/Keshav0375/FinAdvisor/issues/163"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Extract suitability rules with Haiku structured output, validate them and write suitability_rules.

## Description
Arch (4.7 `contextualizer`; 5.2 `suitability_rules`; Flow 2): 'suitability-rule extraction (Haiku structured output, validated) into `suitability_rules`'. Columns: `rule_name, product_category, client_risk_profile` (CHECK conservative/moderate/aggressive), `min_tier_required`, `jurisdiction`, `regulatory_ref`, `rule_text` (redacted), `source_document_id` (composite FK), `extractor_model`, `validated_at`, `last_reviewed_at`. Run in the contextualizer for documents with `doc_type` indicating suitability rules; use a Pydantic output schema; validation rejects rows with an out-of-enum risk profile, tier outside 1..4, or missing regulatory_ref and records them in `ingest_rejects` (stage `suitability`) instead of inserting. Valid rows are upserted idempotently (key on tenant, source_document_id, rule_name, product_category, client_risk_profile). `validated_at` is set only on validated rows. Out of scope: the `lookup_suitability_rule` tool itself (E3-T11).

## Acceptance criteria
- [ ] Given the synthetic corpus for tenant A, when the pipeline completes, then `suitability_rules` has >=1 row for each of conservative, moderate, aggressive and every row has `validated_at` not null (integration)
- [ ] Given a model output with risk profile 'reckless', when validated, then no row is inserted and an `ingest_rejects` row with stage 'suitability' exists (test)
- [ ] Given a rerun, when extraction repeats, then the row count is unchanged (test)
- [ ] Given a real DB with the corpus loaded, when E3's `lookup_suitability_rule('equities','moderate')` runs for tenant A, then it returns >=1 row (integration test)
