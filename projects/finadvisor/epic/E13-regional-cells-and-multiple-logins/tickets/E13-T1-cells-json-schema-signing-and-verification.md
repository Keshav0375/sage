---
key: "E13-T1"
title: "cells.json schema, signing and verification"
epic: "E13"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E1-T4"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.11", "deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "decision-logs.md#adr-031"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 314, "id": 6263812893, "url": "https://github.com/Keshav0375/FinAdvisor/issues/314"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
A typed, signed `cells.json` document can be built, signed and verified, and a tampered or older file is rejected.

## Description
Implements deep-dive/06 §6.11: "`cells.json` is signed and stored in GCS with a baked fallback in the image ... `residency_class` in (`none`, `eu_only`, `uk_only`). `state` in (`active`, `moved`). A higher `version` replaces a lower one atomically; a cell never applies an older version."

Build `backend/app/cells/model.py` (Pydantic): `CellsFile{schema_version:int, version:int, issued_at, cells:[{cell_id, region, api_endpoint, deployed}], tenants:[{slug, tenant_id, idp_tenant_id, home_cell, residency_class, state}], signature:{alg, key_id, value}}`. Validators: `home_cell` names a listed cell, `slug` and `tenant_id` unique, enums as above.
Build `backend/app/cells/signing.py`: `canonical_bytes(doc)` = the document without `signature`, serialized as RFC 8785 JSON Canonicalization (JCS); `sign`, `verify` with Ed25519, `signature.alg = "Ed25519"`, public key from `CELLS_PUBLIC_KEY` (set in E13-T1 per orchestrator). CLI `backend/scripts/cells_sign.py --in unsigned.json --key <path> --out cells.json` (used by onboarding and by the move protocol). Commit a baked fallback `backend/app/cells/cells.fallback.json` signed with a dev test key, plus a generator for the compose test keys.

Out of scope: reading from GCS or refreshing (E13-T2), `/resolve`, Cloud KMS key management.

## Acceptance criteria
- [ ] Given a document signed by `cells_sign.py`, when `verify` runs with the matching public key, then it returns true (`test_cells_signing.py::test_roundtrip`).
- [ ] Given the signed file with one byte of a tenant entry changed, when `verify` runs, then it returns false (`test_cells_signing.py::test_tamper_rejected`).
- [ ] Given two documents equal except for JSON key order and whitespace, when canonicalized, then the bytes are identical (`test_cells_signing.py::test_jcs_stable`).
- [ ] Given a `home_cell` not in `cells`, a duplicate `slug`, or `residency_class: "us_only"`, when the model validates, then it raises `ValidationError`; and a file with `version` 42 replaces 41 but an equal or lower version never replaces (`test_cells_model.py`).
