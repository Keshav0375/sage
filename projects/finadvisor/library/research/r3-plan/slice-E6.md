# Slice E6

## Epic section (from arch/plan.md)

### E6 ETL and data engineering

- **Goal.** A replayable, idempotent pipeline from raw documents to tenant-scoped, redacted, embedded chunks and analytics.
- **Scope.**
  - Bronze (GCS by sha256); silver (Docling, Presidio, structure-aware chunking with Voyage token counts, Pandera, rejects; Parquet partitioned tenant / dt); contextual headers (Haiku batch, flag); suitability-rule extraction and validation; embed-indexer upserts (unique `(tenant_id, chunk_hash, embed_model)`) that bump `corpus_version`.
  - Dagster assets / partitions run daemon-less as Cloud Run jobs from Scheduler, with Postgres run storage (`dagster` database, `fa_dagster`); `dagster dev` locally. Tenant stages run as worker consumers; PUBLIC (EDGAR 497K) runs all stages in-process in `etl-public` and publishes only analytics events. Synthetic per-tenant corpus.
  - dbt gold as `fa_dbt` (`security_invoker` views or incremental models, never full rebuilds); `dbt-bigquery` marts; BigQuery sink with per-tenant authorized views (primary) and row access policies (second layer).
  - ACL change as metadata UPDATE (applier from E5).
- **Arch sections.** overview.md#4.7 to #4.11, overview.md#4.14 (flow 2), overview.md#5.2, overview.md#5.8; ADR-014, ADR-016.
- **Dependencies.** E5.
- **Spikes first.** Docling on the 497K HTML and inline-XBRL tables (chunk sizes measured with Voyage `count_tokens`).
- **Done when.**
  - Re-running the same partition re-embeds zero unchanged chunks (count asserted); an ACL change updates metadata with zero embed calls.
  - Every Pandera failure appears in `ingest_rejects`; no raw document text exists outside GCS bronze (scan test of `documents`, `chunks`, events, BigQuery).
  - `suitability_rules` is populated and validated for the synthetic corpus; `lookup_suitability_rule` returns rows on a real DB.
  - dbt gold models pass the CI assertion that every tenant-schema table has RLS enabled, forced, with policies, and no dbt run does a full-table rebuild of a tenant table; only `fa_tenant_lookup` is `SECURITY DEFINER`.
  - The PUBLIC corpus is written only by `fa_etl_public` (test: a worker attempt is denied by policy and a PUBLIC event on a pipeline topic is sent to `dlq.v1`).
  - BigQuery tables are day-partitioned, clustered by `tenant_id`, with `maximum_bytes_billed` set; a tenant's authorized view returns only that tenant's rows.
  - Fixes G-07, G-39, G-62.

## Arch files to read (paths; read only the named subsections)

- context/projects/finadvisor/arch/overview/04-components-and-responsibilities.md  (sections: 4.14, 4.7)
- context/projects/finadvisor/arch/overview/05-data-model-and-storage.md  (sections: 5.2, 5.8)
- context/projects/finadvisor/arch/stack.md (versions)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md §6.6 (config keys), only the keys this epic uses

## ADRs (context/projects/finadvisor/arch/decisions.md; line of heading)

- line 219: ADR-014: ETL stack: Dagster, dbt, BigQuery, bronze/silver/gold
- line 177: ADR-016: Contextual retrieval at ingest, behind a flag
