---
key: "E13-T3"
title: "GET /resolve?slug= from the signed directory"
epic: "E13"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E13-T2", "E2-T12", "E1-T16"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.11", "deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "decision-logs.md#adr-031"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 323, "id": 6263828810, "url": "https://github.com/Keshav0375/FinAdvisor/issues/323"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
The SPA can resolve a tenant slug to its cell and per-cell API endpoint without a database.

## Description
Implements: "`GET /resolve?slug=` (public, rate limited by IP, served from the same signed file by a Kong route or edge function; set in E13) returns `{cell_id, api_endpoint}`. The SPA then talks to the per-cell hostname" (06 §6.11). Serving choice set in E13-T3 per orchestrator: a Kong route to a small chat-api endpoint backed by `CellDirectory` (E13-T2).

Add `GET /resolve?slug=`: `200 {"cell_id","api_endpoint"}` for a known slug, no DB access; `404 TENANT_NOT_FOUND` otherwise (standard error envelope). For a `moved` tenant it returns the new home cell. Add the public Kong route in `kong.yml` (no auth, same IP rate limit as the E1-T16 discovery route). Never expose `tenant_id` or `idp_tenant_id`.

Out of scope: the SPA call (E8), hostnames and ALB host rules (E2, E10).

## Acceptance criteria
- [ ] Given slug `alpha` homed in `us`, when `GET /resolve?slug=alpha` is called, then the body is exactly `{cell_id:"us", api_endpoint:...}` and the DB query log is empty (`test_resolve.py::test_known_slug_no_db`).
- [ ] Given an unknown slug, then 404 `TENANT_NOT_FOUND` with the standard envelope (`test_resolve.py::test_unknown_slug`).
- [ ] Given an entry `moved` to `eu`, then the `eu` endpoint is returned (`test_resolve.py::test_moved_returns_new_cell`).
- [ ] Given more requests from one IP than the Kong limit, when the compose smoke script calls the route, then it receives 429 `RATE_LIMITED` (`make smoke-resolve-rate`).
