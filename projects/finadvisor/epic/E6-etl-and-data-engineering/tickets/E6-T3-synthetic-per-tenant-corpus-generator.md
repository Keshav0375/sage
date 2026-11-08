---
key: "E6-T3"
title: "Synthetic per-tenant corpus generator"
epic: "E6"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E6-T2"]
arch_refs: ["deep-dive/04-1-key-flows.md#4.14", "decision-logs.md#adr-014"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 157, "id": 6263517061, "url": "https://github.com/Keshav0375/FinAdvisor/issues/157"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Generate a deterministic synthetic document corpus for each tenant, including suitability-rule documents.

## Description
Plan E6: 'Synthetic per-tenant corpus.' ADR-014 data input: synthetic per-tenant corpus plus a real public source. Existing seed data lives in `data/corpus/` (compliance_memos, jurisdiction_disclosures, product_factsheets, suitability_rules). Build `backend/src/etl/synthetic/` with a seeded generator `generate(tenant_slug, seed, n_docs)` writing documents to a local dir (HTML or Markdown) with fields: title, doc_type, jurisdiction, tier_required (1..4), regulatory_ref, last_reviewed_at, product_category, risk_level. Per tenant, include at least 3 suitability-rule documents covering the 3 client risk profiles (conservative, moderate, aggressive) and documents containing synthetic PII (names, emails, SSN-like strings) so the Presidio stage has something to scrub. Documents differ per tenant (tenant-specific names and thresholds) so cross-tenant leakage is detectable. Out of scope: uploading to GCS (E6-T4), real EDGAR data (E6-T13).

## Acceptance criteria
- [ ] Given the same seed twice, when the generator runs, then the output files have identical sha256 (test)
- [ ] Given two tenants, when generated, then no document sha256 appears in both (test)
- [ ] Each tenant corpus contains >=3 suitability-rule docs spanning conservative, moderate, aggressive (test counts by profile)
- [ ] Each tenant corpus contains planted PII strings recorded in a sidecar manifest file used by E6-T5/T14 tests
