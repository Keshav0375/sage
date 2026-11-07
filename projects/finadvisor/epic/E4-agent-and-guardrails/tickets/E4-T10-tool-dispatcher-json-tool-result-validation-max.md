---
key: "E4-T10"
title: "Tool dispatcher: JSON tool_result, validation, max iterations"
epic: "E4"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E4-T4", "E3-T9", "E3-T10", "E3-T11"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.3", "deep-dive/04-components-and-responsibilities.md#4.5", "decision-logs.md#ADR-007"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 102, "id": 6155689535, "url": "https://github.com/Keshav0375/FinAdvisor/issues/102"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Dispatch the four tools with Pydantic validation, JSON-encoded results and no exception text.

## Description
In src/agent/tools, per 6.3: unknown tool names rejected; arguments validated by Pydantic models (search_firm_kb top_k bounded; lookup_product_factsheet product_name; lookup_suitability_rule product_category and enum client_risk_profile); no tool accepts tenant, tier, jurisdiction or licenses (tests assert the schemas lack those fields); output is model_dump_json(); failures return {"error_code": ...} with no exception text; iterations capped at LLM_MAX_ITERATIONS (3). Retrieved text only ever appears in a tool_result block, never in system. Tools call the E3 services (search_firm_kb, factsheet, suitability) through RetrievalService(principal); this ticket does not reimplement them. Tool definitions registered for the prompt-cache builder (E4-T7).

## Acceptance criteria
- [ ] Given a tool call with an unknown name, when dispatched, then the result is {"error_code":"UNKNOWN_TOOL"} and no service is called.
- [ ] Given a tool raising ValueError('secret sql'), when dispatched, then the tool_result JSON contains error_code and the string 'secret sql' appears nowhere in it (test).
- [ ] Given every tool's JSON schema, when inspected, then no property named tenant_id, tier, jurisdiction or licenses exists.
- [ ] Given a model that requests tools 4 times, when the loop runs, then it stops after 3 iterations.
