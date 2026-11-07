---
key: "E6-T15"
title: "dbt project and Postgres gold models as fa_dbt"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T8", "E6-T10"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/04-components-and-responsibilities.md#4.8", "decision-logs.md#adr-014", "decision-logs.md#adr-034"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Create the dbt project with gold models documents_current, stale_documents and corpus_stats, each under an enforced contract.

## Description
Arch (5.2 Gold layer; 4.8 `dbt`): 'Gold layer (dbt, `fa_dbt`, which owns schema `gold`...): models `gold.documents_current`, `gold.stale_documents` and `gold.corpus_stats`; views with `security_invoker = true`, or incremental models with a tenant predicate (never full-table rebuilds)'; 'per tenant run on a dedicated connection'. Create `dbt/` with `dbt-postgres`; the three models as `security_invoker` views over RLS-protected tables (documents status='active' for current; stale = `last_reviewed_at` older than the staleness config; corpus_stats counts docs/chunks/tokens per tenant). Run per tenant via `jobs dbt --tenant <slug>` setting `app.tenant_id` on a dedicated connection. A post-hook sets `security_invoker = true`. Round 4 (ADR-014 amended, ADR-034): every gold model that is a table or incremental model declares `contract: {enforced: true}` with typed `columns` in its YAML (views are checked by dbt tests); a column type drift fails the build. Out of scope: BigQuery marts (E6-T18), CI assertions (E6-T16).

## Acceptance criteria
- [ ] Given tenants A and B, when dbt runs as fa_dbt for tenant A, then `gold.documents_current` returns only tenant A rows (integration).
- [ ] Given the built views, when `pg_class.reloptions` is read, then each gold view has `security_invoker=true`.
- [ ] Given a gold table or incremental model whose SQL returns a column of a different type than its YAML contract, when `dbt build` runs, then it fails with a contract error (test_dbt_contract_enforced; a project scan asserts `contract.enforced: true` on every non-view model).
- [ ] Given a doc with `last_reviewed_at` > staleness limit, when queried, then it appears in `gold.stale_documents` (dbt test); `dbt test` passes in CI against the compose Postgres.
