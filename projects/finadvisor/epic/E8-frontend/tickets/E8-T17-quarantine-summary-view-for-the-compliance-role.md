---
key: "E8-T17"
title: "Add the quarantine summary view for the compliance role"
epic: "E8"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E8-T4", "E11-T28"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.8", "deep-dive/06-interfaces-and-contracts.md#6.8", "decision-logs.md#adr-036"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Compliance officers see counts of quarantined documents by source and reason, and other roles do not see the view.

## Description
Implements the R4 E8 line "a quarantine view for the compliance role (summary only, never raw quarantined text)" (ADR-036, 8.8). A route `/t/:slug/quarantine` that calls `GET /v1/admin/quarantine/summary` (E11-T28) with the active firm's token and renders a table: source id, reason code (client-owned label per code, unknown code shown as the raw code text), count, oldest date. The nav entry and the route render only when `/v1/me` role is `compliance_officer` or `tenant_admin` (E8-T3); for other roles the route shows the FORBIDDEN state of E8-T4 and no request is sent. All values render as text. The view has no action buttons (release and reject are admin CLI only).

Out of scope: the endpoint (E11-T28), release or reject.

## Acceptance criteria
- [ ] Given role `compliance_officer` and a mocked summary of 2 rows, when /t/acme/quarantine renders, then 2 rows with source, reason and count show (vitest `quarantine.test.tsx::renders_rows`).
- [ ] Given role `advisor`, when the nav and route render, then the nav entry is absent, the route shows the FORBIDDEN state and no request to the summary endpoint is made (vitest, request spy).
- [ ] Given a mocked row with reason `<b>x</b>`, when rendered, then it appears as literal text with no <b> element.
- [ ] Given the Playwright harness, when an advisor and a compliance officer sign in, then only the officer sees the nav entry (spec `quarantine.spec.ts`).
