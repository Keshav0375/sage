---
key: "E13-T12"
title: "Privacy notice: residency wording and global-data list"
epic: "E13"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E13-T1"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.7", "deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "decision-logs.md#adr-038", "decision-logs.md#adr-031"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
The privacy notice states the residency promise exactly as decided and declares the global data and the provider-outage limit.

## Description
Implements ADR-038 wording: "Data at rest (database, search index, document store, warehouse, event streams, traces) stays in the tenant's home cell, except the declared global data (ADR-031). Prompt text and embedding and rerank inputs are processed by Anthropic and Voyage, which are US/global." Global data (ADR-031): user id, email, firm membership, tenant-to-cell map, PUBLIC manifest hashes, aggregate metrics. Also: cells do not isolate an LLM-provider outage; no EU-only processing claim; `llm_egress_ack` must be true before private ingest (the gate itself is tested in E11). Notice location `docs/privacy-notice.md`, set in E13-T12 per orchestrator.

Create `docs/privacy-notice.md` with sections: Residency (the quoted sentence, verbatim), Global data (the list), LLM providers (the three egress paths: Anthropic prompt, Voyage embedding, Voyage rerank; provider retention is outside the erasure promise), Provider outages, Langfuse traces stay in the home cell. Add a test that guards the wording.

Out of scope: legal review, footer wording for publisher documents, the `llm_egress_ack` implementation.

## Acceptance criteria
- [ ] Given `docs/privacy-notice.md`, then it contains the ADR-038 residency sentence verbatim (`tests/docs/test_privacy_notice.py::test_residency_sentence`).
- [ ] Then it lists all six global-data items (user id, email, firm membership, tenant-to-cell map, PUBLIC manifest hashes, aggregate metrics) (`test_privacy_notice.py::test_global_data_list`).
- [ ] Then it states that cells do not isolate an LLM-provider outage and does not contain the phrases "EU-only processing" or "zero retention" (`test_privacy_notice.py::test_no_overclaims`).
- [ ] Then it names the three egress paths and `llm_egress_ack` (`test_privacy_notice.py::test_egress_paths`).
