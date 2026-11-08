---
key: "E13-T5"
title: "Token tenant must equal URL tenant and cell map entry"
epic: "E13"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E13-T4", "E1-T13"]
arch_refs: ["deep-dive/08-security-and-privacy.md#8.2", "deep-dive/06-interfaces-and-contracts.md#6.11", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.4", "decision-logs.md#adr-032"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 325, "id": 6263831064, "url": "https://github.com/Keshav0375/FinAdvisor/issues/325"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
A token issued for one firm cannot act on another firm's resource: the server compares `firebase.tenant`, the URL tenant and the directory entry.

## Description
Implements: "The server verifies at project level, reads `firebase.tenant` and requires it to equal the tenant in the URL and the signed `cells.json` entry; a mismatch is 403 or 421" (08 §8.2 step 8; 06 §6.11; ADR-032). Edge case #17, server side.

In `auth` and `principal` (E1-T13, E13-T4): after project-level `verify_id_token`, require `firebase.tenant == directory.by_slug(url_tenant).idp_tenant_id`. If the URL tenant is homed in another cell, E13-T4's 421 applies first; otherwise a mismatch is `FORBIDDEN` 403 with no DB read. Identity is never an input across firms: only the claim, the URL tenant and the directory are used.

Out of scope: browser sessions and `currentUser` (E8, the browser half of #17).

## Acceptance criteria
- [ ] Given a valid token for firm A's IdP tenant, when sent to firm B's resource in the same cell, then 403 `FORBIDDEN` and an empty DB query log (`test_token_tenant.py::test_token_a_on_firm_b`, #17).
- [ ] Given the same token sent to a tenant homed in another cell, then 421 and no DB read (`test_token_tenant.py::test_token_a_on_other_cell_firm`).
- [ ] Given claim, URL tenant and directory entry all equal, then the request proceeds (`test_token_tenant.py::test_match_ok`).
- [ ] Given a directory `idp_tenant_id` that differs from the token claim for the same slug, then 403 (`test_token_tenant.py::test_directory_mismatch`).
