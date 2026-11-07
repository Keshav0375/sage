---
key: "E3-T12"
title: "Enforce RetrievalService as sole content-table accessor"
epic: "E3"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E3-T9", "E3-T10", "E3-T11"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.5", "deep-dive/05-data-model-and-storage.md#5.3", "decision-logs.md#adr-004"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 72, "id": 6155655634, "url": "https://github.com/Keshav0375/FinAdvisor/issues/72"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Add an import-linter contract and tests so only the retrieval module touches content tables and fa_app cannot write them.

## Description
Enforce ADR-004 by tooling. Prerequisite: the tools and any other chat-api module no longer query `chunks`, `documents` or `suitability_rules` directly (E3-T9, T10, T11); delete the old direct accessor `backend/src/retrieval/vector_store.py` and any remaining direct SQL in `agent`, `api` or `db` modules for these tables.

Arch (§4.5): "Single deployable, modular monolith. Import-linter contracts enforce the boundaries below, plus a test. DB login role `fa_app`: SELECT only on content tables, no write on content tables anywhere in `chat-api`." `retrieval`: "Only module allowed to touch content tables (`documents`, `chunks`, `suitability_rules`), read-only." §5.3: `fa_app` "SELECT on `chunks`, `documents`, `suitability_rules` (read-only: no write grant on any content table)... Content tables are touched only by the `retrieval` module (import-linter + test)". ADR-004: "`fa_app` has SELECT only on content tables".

Deliver: (1) `.importlinter` (or pyproject section) with a `forbidden` contract: the content-table accessor modules (`retrieval._content` or whichever internal module holds the SQL; public surface is `retrieval.service.RetrievalService` only) may be imported by no module outside `retrieval`; wire `lint-imports` into the existing CI job so it fails the PR. (2) A test that scans `backend/src/**/*.py` outside `retrieval/` for the table names `chunks`, `documents`, `suitability_rules` in SQL strings (regex `\b(from|join|into|update)\s+(chunks|documents|suitability_rules)\b`, case-insensitive) and fails on a match. (3) A DB test connected as `fa_app` that asserts INSERT, UPDATE and DELETE on each of the three content tables (and a direct partition of `chunks`) raise `permission denied`, and SELECT through the parent succeeds.

Scope: the `chat-api` package only; worker and job code that legitimately holds other roles is out of scope (see questions on package layout). Out of scope: changing grants (E1 owns them; this ticket only tests).

## Acceptance criteria
- [ ] Given a deliberately added `from src.retrieval._content import x` in `src/agent/tools/foo.py` when `lint-imports` runs then it exits non-zero naming the contract (test `backend/tests/test_import_contracts.py::test_forbidden_import_is_caught`, which runs lint-imports against a temp module).
- [ ] Given a string `'SELECT * FROM chunks'` placed in a module outside `retrieval` when the scan test runs then it fails; on the clean tree it passes (test `test_no_content_sql_outside_retrieval`).
- [ ] Given a connection as `fa_app` when INSERT, UPDATE and DELETE are issued against `chunks`, `documents` and `suitability_rules` then each raises `permission denied`, and the same against a tenant partition of `chunks` also raises `permission denied` (test `backend/tests/test_roles_content_readonly.py::test_fa_app_cannot_write_content`, `integration`).
- [ ] CI runs `lint-imports` as a required step: the workflow file contains the step and the job fails when the contract is broken (checked by `test_ci_runs_lint_imports` reading the workflow YAML).
