---
key: "E6-T15"
title: "dbt project and Postgres gold models as fa_dbt"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T8", "E6-T10"]
arch_refs: ["deep-dive/05-data-model-and-storage.md#5.2", "deep-dive/04-components-and-responsibilities.md#4.8", "decision-logs.md#adr-014"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Create the dbt project with gold models documents_current, stale_documents and corpus_stats.

## Description
Arch (5.2 Gold layer; 4.8 `dbt`): 'Gold layer (dbt, `fa_dbt`, which owns schema `gold`...): models `gold.documents_current`, `gold.stale_documents` and `gold.corpus_stats`; views with `security_invoker = true`, or incremental models with a tenant predicate (never full-table rebuilds)'; 'per tenant run on a dedicated connection'. Create `dbt/` project with `dbt-postgres`; the three models as `security_invoker` views over RLS-protected tables (documents status='active' for current; stale = `last_reviewed_at` older than the staleness config; corpus_stats counts docs/chunks/tokens per tenant). Run per tenant via `jobs dbt --tenant <slug>` setting `app.tenant_id` on a dedicated connection. A custom materialization/post-hook sets `security_invoker = true`. Out of scope: BigQuery marts (E6-T18), CI assertions (E6-T16).

## Acceptance criteria
- [ ] Given tenants A and B, when dbt runs as fa_dbt for tenant A, then `gold.documents_current` returns only tenant A rows (integration)
- [ ] Given the built views, when `pg_class.reloptions` is read, then each gold view has `security_invoker=true` (test)
- [ ] Given a doc with `last_reviewed_at` > staleness limit, when queried, then it appears in `gold.stale_documents` (dbt test)
- [ ] `dbt test` passes in CI against the compose Postgres
