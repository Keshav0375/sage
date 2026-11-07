---
key: "E4-T30"
title: "Role policy table policy.py with default deny and CI matrix"
epic: "E4"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E4-T10"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.8", "deep-dive/06-interfaces-and-contracts.md#6.3", "deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#adr-036"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Define the role x tool x output-field policy as data, default deny, and fail CI when a tool has no policy row.

## Description
Implement `agent/policy.py` (ADR-036 decision 6; 8.8: 'Role policy lives in `policy.py` as a table of role x tool x output field, default deny. A tool without a policy row fails CI; the role x tool matrix test is generated from the table.'). Table rows: role `advisor`: tools `search_firm_kb`, `lookup_product_factsheet`, `lookup_suitability_rule`, `calc`, `escalate_to_compliance`, output fields quote cap, `show_raw_excerpt`, internal notes off; role `compliance_officer`: advisor tools plus the quarantine summary (never raw quarantined text) and full excerpts of the tenant's documents; role `tenant_admin`: no LLM tools (admin is API only). The dispatcher (E4-T10) consults `policy.allowed(role, tool)` before calling any tool and returns {"error_code":"TOOL_NOT_PERMITTED"} (no service call) for a denied pair; output fields are filtered by the policy before they reach the tool_result. Add a pytest that enumerates the registered tools and fails if one has no row, and a test generated from the table over the full role x tool grid. Out of scope: the `calc` tool itself (E4-T33), the quarantine summary endpoint (E11).

## Acceptance criteria
- [ ] Given a tool registered without a policy row, when the CI test runs, then it fails naming the tool (negative fixture proves it fails; real registry passes).
- [ ] Given the role x tool grid generated from the table, when each cell is dispatched, then allowed cells call the service and denied cells return TOOL_NOT_PERMITTED with zero service calls (generated parametrised test).
- [ ] Given role tenant_admin, when it attempts any LLM tool, then every call is denied; given an unknown role, every tool is denied (default deny).
- [ ] Given the advisor role, when a tool result is built, then fields outside its output-field policy are absent from the tool_result JSON.
