---
key: "E13"
title: "Tools rewrite"
phase: 3
phase_name: "Backend (MVP release)"
repo: "Sentinel"
status: "done"
depends_on: ["E12"]
arch_refs: ["deep-dive/04-agent-pipeline.md#4.4", "ADR-033", "ADR-004"]
issue: {"repo": "Keshav0375/sentinel-brain", "number": 59, "id": 5694997230, "url": "https://github.com/Keshav0375/sentinel-brain/issues/59"}
updated: "2026-11-08"
---

## Goal
The six tools on real sources (Postgres, Datadog, GitHub) and removal of the POC comms and approval tools.

Source: backend phase 3 · branch `dev/backend-phase-3-tools` · PR https://github.com/Keshav0375/Sentinel/pull/21 · signed 2026-10-14.

## Scope
- E13-T1: config.py extensions
- E13-T2: get_service_metadata → PostgreSQL
- E13-T3: search_past_incidents → pgvector
- E13-T4: fetch_logs → Datadog Logs API
- E13-T5: get_deploy_details → PostgreSQL + GitHub API
- E13-T6: prepare_rollback_spec + format_escalation
- E13-T7: Remove comms_tools.py + hitl.py

## ADRs
[ADR-033](../../arch/decision-logs.md#adr-033), [ADR-004](../../arch/decision-logs.md#adr-004)

## Exit criteria
- [x] Every ticket built, tested and gated `VERDICT GREEN` (full run)
- [x] Phase review: architecture conformance, code and (where relevant) safety reviewers clean
- [x] Owner sign-off and PR merged

## Outcome
Exactly six tools, all read-only or pure; `ToolFailure` results; compact JSON outputs; an untrusted-data preamble on every agent prompt; size caps. 1634 tests.
