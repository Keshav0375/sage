---
key: "E4-T33"
title: "Deterministic calc tool with grounded inputs"
epic: "E4"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E4-T10"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.6", "deep-dive/08-security-and-privacy.md#8.8", "deep-dive/06-interfaces-and-contracts.md#6.3", "decision-logs.md#adr-036"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Add the deterministic calc tool the numeric gate requires for derived figures, recording its inputs.

## Description
The numeric gate allows derived figures 'only from a deterministic `calc` tool whose inputs are grounded' (8.6), and 8.8 lists `calc` among the advisor tools. Add `calc` to the E4-T10 dispatcher: arguments `{operation: "add"|"sub"|"mul"|"div"|"pct_of"|"bps_to_pct", operands: [decimal string, ...]}` validated by Pydantic (decimal strings only, at most 8 operands, `div` by zero returns {"error_code":"DIVISION_BY_ZERO"}); computation with `decimal.Decimal` in a fixed context (no float, no eval, no model call); the result is `{value: "<decimal>", operands: [...], operation}` as model_dump_json so E4-T28 can check that each operand is grounded in a cited span. No tenant, tier, jurisdiction or as_of argument. A policy row for `calc` is added by E4-T30. The argument shape is set in E4-T33 per orchestrator (R4-D20). Out of scope: the grounding check itself (E4-T28).

## Acceptance criteria
- [ ] Given operation `pct_of` with operands ['1234.56','2.5'], when dispatched, then value equals Decimal('30.864') exactly and the result echoes the operands (unit test; no float rounding drift over a property test of 1000 random decimals vs Decimal arithmetic).
- [ ] Given operation `div` with a zero divisor, then {"error_code":"DIVISION_BY_ZERO"} with no exception text.
- [ ] Given the calc schema, when inspected, then no property named tenant_id, tier, jurisdiction, licenses or as_of exists, and operand strings that are not decimals are rejected with a validation error_code (test).
