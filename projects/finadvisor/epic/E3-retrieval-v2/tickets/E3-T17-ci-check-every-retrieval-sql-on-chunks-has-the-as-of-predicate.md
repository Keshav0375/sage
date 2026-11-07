---
key: "E3-T17"
title: "CI check: SQL on chunks and document_versions has as_of predicate"
epic: "E3"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E3-T5", "E3-T8"]
arch_refs: ["deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.6", "decision-logs.md#adr-027", "deep-dive/04-components-and-responsibilities.md#4.5"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
A CI test fails any SQL string in the retrieval module that reads `chunks` without the as-of predicate.

## Description
Arch (deep-dive/05-1 section 5.6): "RLS is isolation, not time: a forgotten `as_of` predicate would give a stale answer, not a leak, so a CI test requires `valid_range @> ` in every SQL string of the retrieval module and a second check runs after generation (section 4.18)." ADR-027 and plan E3 (Round 4 changes): "a CI check fails any retrieval SQL without the predicate".

Add `backend/tests/test_retrieval_as_of_predicate.py`, run in the unit job (no database): it collects every SQL string literal under `backend/src/retrieval/` (by AST walk over string constants and f-strings passed to the DB layer) that names the table `chunks` after `FROM`, `JOIN` or `UPDATE`, and asserts each contains `valid_range @>` and `upper_inf(system_range)`. A small allow-list file `backend/tests/as_of_allowlist.txt` may name statements exempt by a stable id (none at the start); every entry needs a one-line reason, and the test fails when an allow-list entry no longer matches a statement. Statements on `documents` and `suitability_rules` are outside this check (they have no `valid_range`; the arch states the rule for the hybrid statement and chunk reads, see the report question).

Out of scope: the post-generation validity check (E4), changing any statement (E3-T5, E3-T8 own them).

Scope (orchestrator decision): the check covers SQL on the two tables that carry `valid_range`, `chunks` and `document_versions`; statements on `documents` and `suitability_rules` are outside it. For `document_versions` the test requires `valid_range @>` (and `upper_inf(system_range)`) in each retrieval-module statement that reads it.

## Acceptance criteria
- [ ] Given the clean tree, then the test passes and reports the number of checked statements (at least 3: the two legs of `search` counted as one string, `expand_parents`, `fetch_chunks`).
- [ ] Given a temporary module under `src/retrieval/` containing the string `SELECT id FROM chunks WHERE kind = 'child'`, then the test fails and names the file and line (`test_missing_predicate_is_caught`, using a temp copy of the package).
- [ ] Given an allow-list entry that matches no statement, then the test fails (`test_stale_allowlist_entry_fails`).
- [ ] Given the CI workflow, then the unit job runs this test (`tests/ci/test_ci_runs_as_of_check.py` reads the workflow YAML for the step).
- [ ] Given a temporary module under `src/retrieval/` containing `SELECT id FROM document_versions WHERE doc_id = $1`, then the test fails and names the file and line (`test_missing_predicate_on_document_versions_is_caught`).
