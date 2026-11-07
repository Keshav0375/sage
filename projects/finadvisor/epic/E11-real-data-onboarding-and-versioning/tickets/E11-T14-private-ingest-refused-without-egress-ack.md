---
key: "E11-T14"
title: "Private ingest refused without llm_egress_ack"
epic: "E11"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E1-T4", "E6-T4"]
arch_refs: ["decision-logs.md#adr-38", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.12", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4 (#26)"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Refuse private ingest for a tenant whose llm_egress_ack is false, with zero provider calls.

## Description
Add the egress check at the start of every private ingest path (the `publisher` connector and any firm upload).

Arch (5.12, ADR-038): `tenants.llm_egress_ack boolean NOT NULL DEFAULT false` must be true before private ingest for the tenant; private text reaches Anthropic and Voyage (embed and rerank), so refusal is before any provider call. Add the column in a migration if the E1 baseline lacks it (check first; the plan places tenant flags with E13 for `cell_id` only). Enabled explicitly for the demo tenants via the onboarding seed. PUBLIC law ingest is unaffected. The flag records acceptance of the egress paths; it is not a residency or zero-retention claim.

Out of scope: the other two egress paths' runtime behaviour (query-time embed/rerank, E3/E4) beyond the stub recording below.

## Acceptance criteria
- [ ] Given a tenant with `llm_egress_ack=false` when a private ingest is requested then it is refused with a stable error code and the stub embedding, contextualizer and LLM clients record zero calls (#26; test `backend/tests/ingest/test_egress_ack.py::test_refused_with_zero_provider_calls`, PR).
- [ ] Given `llm_egress_ack=true` then ingest proceeds and the stub providers record that private text left on the ingest paths (test `test_private_text_leaves_only_when_flag_true`).
- [ ] Given a PUBLIC ingest with the PUBLIC tenant flag false then ingest proceeds (test `test_public_ingest_unaffected`).
