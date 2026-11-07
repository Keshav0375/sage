> Part of [architecture](../architecture.md) · [diagram](../architecture-diagram.md)
### 5.4 Row-level security

All tenant tables: `ENABLE` and `FORCE ROW LEVEL SECURITY`. Settings are transaction-local, set only by `principal`: `SELECT set_config('app.tenant_id', $1, true), set_config('app.idp_uid', $2, true), set_config('app.user_id', $3, true), set_config('app.role', $4, true), set_config('app.tier', $5, true), set_config('app.jurisdictions', $6, true)` with bind parameters. Policies call `current_setting('app.x')` without `missing_ok`, so an unset setting raises an error (fail closed). `<PUBLIC>` below is the `PUBLIC_TENANT_ID` uuid literal substituted by the Alembic migration, so a request cannot change it.

SELECT is own tenant OR PUBLIC. INSERT / UPDATE / DELETE is own tenant only and never PUBLIC (D13a). Policy text for `chunks` (`documents` and `suitability_rules` are identical in shape; `suitability_rules` uses `min_tier_required`):

```sql
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE chunks FORCE  ROW LEVEL SECURITY;

-- user-facing reads: tenant or PUBLIC, plus tier and jurisdiction
CREATE POLICY chunks_select_app ON chunks FOR SELECT TO fa_app
  USING ( (tenant_id = current_setting('app.tenant_id')::uuid OR tenant_id = '<PUBLIC>'::uuid)
          AND tier_required <= current_setting('app.tier')::int
          AND jurisdiction = ANY (string_to_array(current_setting('app.jurisdictions'), ',')) );

-- pipeline reads: own tenant only
CREATE POLICY chunks_select_pipe ON chunks FOR SELECT TO fa_worker, fa_etl, fa_etl_public, fa_dbt
  USING ( tenant_id = current_setting('app.tenant_id')::uuid );

-- writes by tenant pipelines: own tenant, never PUBLIC (column grants limit UPDATE to ACL columns)
CREATE POLICY chunks_ins_tenant ON chunks FOR INSERT TO fa_worker
  WITH CHECK ( tenant_id = current_setting('app.tenant_id')::uuid AND tenant_id <> '<PUBLIC>'::uuid );
CREATE POLICY chunks_upd_tenant ON chunks FOR UPDATE TO fa_worker
  USING      ( tenant_id = current_setting('app.tenant_id')::uuid AND tenant_id <> '<PUBLIC>'::uuid )
  WITH CHECK ( tenant_id = current_setting('app.tenant_id')::uuid AND tenant_id <> '<PUBLIC>'::uuid );
CREATE POLICY chunks_del_tenant ON chunks FOR DELETE TO fa_worker
  USING ( tenant_id = current_setting('app.tenant_id')::uuid AND tenant_id <> '<PUBLIC>'::uuid );

-- the only writer of PUBLIC
CREATE POLICY chunks_all_public ON chunks FOR ALL TO fa_etl_public
  USING ( tenant_id = '<PUBLIC>'::uuid ) WITH CHECK ( tenant_id = '<PUBLIC>'::uuid );
```

`fa_app` has no INSERT, UPDATE or DELETE policy on `chunks`, `documents` or `suitability_rules`; document ACL changes are applied by the `acl-applier` worker; document deletes are `deletion_requests` rows written by `admin` (tenant_admin) and executed by the `erasure-worker` (ADR-022 amended, ADR-029).

Other tables:
- `tenants`: `tenants_select_app TO fa_app FOR SELECT USING (id = current_setting('app.tenant_id')::uuid OR id = '<PUBLIC>'::uuid)`; `tenants_lookup TO fa_lookup FOR SELECT USING (true)`; `tenants_owner TO fa_owner` for SELECT, INSERT, UPDATE; `tenants_upd_worker TO fa_worker FOR UPDATE USING / WITH CHECK (id = app.tenant_id AND id <> <PUBLIC>)`; `tenants_upd_public TO fa_etl_public FOR UPDATE USING / WITH CHECK (id = <PUBLIC>)`. Column grants limit UPDATE to `corpus_version`, `acl_version` and (PUBLIC row, `fa_etl_public` only) `source_epoch`.
- `advisors`: SELECT `TO fa_app` when `tenant_id = app.tenant_id AND (id = app.user_id OR idp_uid = app.idp_uid OR app.role = 'tenant_admin')` (own row, or every row of the own tenant for a tenant admin); UPDATE `TO fa_app` only when `tenant_id = app.tenant_id AND app.role = 'tenant_admin'`, `WITH CHECK (tenant_id = app.tenant_id)`. No self-escalation: an advisor cannot raise their own tier or role (L0 test "advisor raises own tier / role gives denied").
- `conversations`, `messages`, `turn_events`, `feedback`: tenant match AND `advisor_id = current_setting('app.user_id')::uuid` (an advisor sees only their own rows).
- `escalations`: tenant match AND (`advisor_id = app.user_id` OR `app.role = 'compliance_officer'`).
- `acl_change_requests`: SELECT / INSERT `TO fa_app` when tenant matches and `app.role = 'tenant_admin'`; UPDATE of status columns `TO fa_worker` on the own non-PUBLIC tenant.
- `eval_scores`, `ingest_rejects`, `outbox`, `processed_events`: tenant match for the roles that hold grants (no PUBLIC clause). `answer_cache`: own RLS + FORCE (D13i), tenant match for `fa_app` and `fa_worker`; `fa_maint` may delete expired rows only; `outbox` is also readable by `fa_maint` for unpublished rows.
- `fa_eval` policies equal the `fa_app` policies with the tenant literal of the `eval` tenant.

`fa_tenant_lookup(p_slug text DEFAULT NULL, p_idp_tenant_id text DEFAULT NULL)` is the only `SECURITY DEFINER` function allowed in the database (D13m, D13n); CI fails on any other. It is owned by `fa_lookup` (a dedicated NOLOGIN role, not `fa_owner`), sets `search_path` explicitly, returns `(id, display_name, idp_tenant_id)`, and serves both slug discovery and the `idp_tenant_id` to `tenants.id` mapping (D14.4). `REVOKE EXECUTE ... FROM PUBLIC; GRANT EXECUTE ... TO fa_app;`. The public endpoint returns only display name and IdP tenant id. Policies and grants are covered by E1 tests.

The write split and the PUBLIC rule are tested by the L0 leak matrix: cross-tenant read, cross-tenant insert, update into PUBLIC, delete in PUBLIC, FK existence probes, direct partition access, advisor self-escalation, pooled-connection reuse (§8.5).

### 5.5 Partitioning and indexes

- `chunks`: `PARTITION BY LIST (tenant_id)`: one partition per tenant, one for PUBLIC, plus a DEFAULT partition (rows landing there are a bug and alert). Tenant onboarding (`migrate --onboard-tenant`) creates the partition, its indexes and its `EXCLUDE` constraint (PG16 cannot declare that constraint on the partitioned parent, §5.10); the other indexes are declared on the parent so each partition gets its own. Runtime pruning with the RLS `current_setting` policy was confirmed on a test ("Subplans Removed: 6 of 8"); the same check is repeated for LIST partitions in the E1 leak-matrix test. PUBLIC can be sub-partitioned by source later (trigger > 250k chunks). Why not HASH(8): 4 keys in 8 buckets collide ~59% (D13b, ADR-003).
- Per partition, on `chunks`: HNSW on `embedding halfvec_cosine_ops` with `m = 16`, `ef_construction = 64`, partial `WHERE kind = 'child' AND embed_model = '<model>'` (one index per embedding generation, §5.10); GIN on `tsv`; btree `(tenant_id, document_id)`, `(tenant_id, parent_id)`, `(tenant_id, tier_required, jurisdiction)`, `(tenant_id, chunk_hash, embed_model)` (vector reuse; not unique); unique on the chunk identity (§5.10); GiST from the `EXCLUDE` constraint, which also serves `valid_range` containment. Trigger for a partial index `WHERE is_current` on the default path: recall or p95 misses in the E3 spike (§5.10).
- Query-time settings, per transaction (`SET LOCAL`): `hnsw.iterative_scan = relaxed_order`, `hnsw.max_scan_tuples = 20000`, `hnsw.ef_search` ~80-100 (config `HNSW_EF_SEARCH`). Filtering is applied after the ANN scan in pgvector, so iterative scan is mandatory and it gives no guarantee of full recall when many superseded rows are filtered (https://github.com/pgvector/pgvector ). halfvec supports <= 4,000 dimensions.
- `messages`: RANGE by month, local indexes `(tenant_id, conversation_id, created_at)`; partitions created 3 months ahead by the `maintenance` job. Neither `chunks` nor `messages` partitions carry grants (§5.3).
- `advisors`: unique `(tenant_id, idp_uid)`. `conversations`: `(tenant_id, advisor_id, updated_at DESC)`. `outbox`: partial unpublished index. `answer_cache`: `(expires_at)` and GIN on `source_document_ids`. `documents`: unique `(tenant_id, doc_key)`; `(tenant_id, doc_type, jurisdiction)`. `acl_change_requests` and `deletion_requests`: partial index on `status = 'pending'` for the pollers. Indexes of the round-4 tables are in §5.9 to §5.12.

### 5.6 Hybrid retrieval statement

One statement, RLS applied to both legs, RRF with `k = 60` (`RRF_K`), the as-of predicate and the active embedding generation in both legs:

```sql
WITH dense AS (
  SELECT id, parent_id, row_number() OVER (ORDER BY embedding <=> $1::halfvec) AS r
  FROM chunks WHERE kind = 'child' AND embedding IS NOT NULL
    AND embed_model = '<active_embed_model>'              -- literal from the allow-list
    AND valid_range @> $5::date AND upper_inf(system_range)
  ORDER BY embedding <=> $1::halfvec LIMIT $2),
fts AS (
  SELECT id, parent_id, row_number() OVER (ORDER BY ts_rank(tsv, q) DESC) AS r
  FROM chunks, websearch_to_tsquery('simple', $3) q
  WHERE kind = 'child' AND tsv @@ q
    AND embed_model = '<active_embed_model>'
    AND valid_range @> $5::date AND upper_inf(system_range)
  ORDER BY ts_rank(tsv, q) DESC LIMIT $2)
SELECT id, parent_id, sum(1.0 / (60 + r)) AS rrf
FROM (SELECT * FROM dense UNION ALL SELECT * FROM fts) u
GROUP BY id, parent_id ORDER BY rrf DESC LIMIT $4;
```

`$5` is `as_of` from the resolver (§4.18), never from the model. The RLS policy supplies the tenant / PUBLIC / tier / jurisdiction filter to both legs; partition pruning limits the scan to the caller's tenant and PUBLIC partitions. RLS is isolation, not time: a forgotten `as_of` predicate would give a stale answer, not a leak, so a CI test requires `valid_range @> ` in every SQL string of the retrieval module and a second check runs after generation (§4.18). `ts_rank` is not BM25 (pg_textsearch needs PG17+, not on Cloud SQL PG16). The `embed_model` filter keeps a half-built generation invisible to queries (§5.10).

### 5.7 Answer cache (D9, D13i)

UNLOGGED table `answer_cache`, exact match only, single-turn requests only, TTL 24 h (`ANSWER_CACHE_TTL_S`). Turns that called a side-effect tool (`escalate_to_compliance`) are never cached. `cache_key = sha256(tenant_id, tier, sorted jurisdictions, corpus_version of the tenant and of PUBLIC, acl_version, entitlement_version of the user, prompt_version, model, as_of, embed_model, source_epoch of PUBLIC, normalized redacted question)` (round 4 adds `as_of`, `embed_model` and `source_epoch`; amends ADR-015). Columns: `cache_key`, `answer` (redacted), `citations` (chunk ids, indexes), `source_document_ids uuid[]`, `created_at`, `expires_at`. On a hit the citation verifier and the as-of validity check re-run against freshly fetched chunks under the caller's RLS and staleness is recomputed; any failure is a miss. Purged by the indexer in the same transaction as any version publish, supersede, retire, withdraw or erase of the document (GIN on `source_document_ids`), by the `acl-applier` on ACL change and document delete, by `purge_source` (the `source_epoch` bump makes older rows unreachable and the fan-out deletes them), and by `maintenance` when expired. No semantic cache.

### 5.8 Object and analytics storage

- GCS data bucket: `bronze/{tenant_id}/{sha256}` (raw, immutable), `silver/tenant_id=<id>/doc_id=<id>/version=<id>/` (redacted chunk Parquet), `quarantine/` (failed scan or contract). Soft delete 0, versioning off (§5.14). Lifecycle rules are not specified by the brief.
- BigQuery dataset `fa_analytics`: tables `chat_audit`, `chat_usage`, `eval_events`, `gateway_audit` (from the Cloud Logging sink), `acl_changes`, `ingest_events`; day-partitioned, clustered by `tenant_id`; per-tenant authorized views (primary isolation) plus row access policies (second layer); `maximum_bytes_billed` on every query; dbt-bigquery marts; subjects appear only as `pseudonym_id`; `max_time_travel_hours = 48` on this dataset and on every other dataset (§5.14). FCA content is never written here.
- Conversation state in Postgres only (`conversations`, `messages`), last 6 turns <= 3k tokens sent to the model.

### 5.9 Source registry, observations and document versions (R4-D2, R4-D3; ADR-026, ADR-027)

Bitemporal on PostgreSQL 16 with `daterange` valid time and `tstzrange` system time (https://www.postgresql.org/docs/16/rangetypes.html ), constrained with `EXCLUDE USING gist` (needs `btree_gist`, available on Cloud SQL: evidence-r4.md §2.2; https://www.postgresql.org/docs/16/btree-gist.html ). PostgreSQL 18 `WITHOUT OVERLAPS` is rejected: the arch binds PG16, temporal foreign keys cannot cascade, and PG18 would re-test E0-E3 assumptions (a later, separate ADR). Valid time is when the text was in force (eCFR amendment date, CELEX date, legislation point-in-time date, filing date, KID "accurate as at"); system time is when we learned it. One current belief per document and valid time; older beliefs are closed (`system_range` upper set), never overwritten, so any past answer is reproducible by `known_at`.

| Table | Key | Columns (beyond key) and rules |
|---|---|---|
| `source_registry` | `(tenant_id, source_id)` | `tenant_id` is the target tenant (PUBLIC for public sources, a firm for publisher sources). `connector` (`ecfr`, `sec`, `eurlex`, `legislation_gov_uk`, `fca_api`, `publisher`), `source_class` (`law`, `qa`, `fca_api`, `publisher`), `on_withdraw` (`retire`, `erase`), `cursor jsonb`, `overlap_s` (default 172800 = 48 h), `last_listing_at`, `frozen boolean` and `frozen_reason` (mass-delete breaker, 401 / 403, contract failure rate), `rate_limit_rps`, `enabled`. Cursor and overlap are updated in the same transaction as the observations they cover |
| `source_observations` | `(tenant_id, id)` | Append-only. `source_id` (composite FK), `external_id`, `version_key` (the source's own key, never arrival order), `content_sha256`, `source_ts`, `observed_at` (DB clock), `state` in (`present`, `revoked`, `withdrawn`, `pending`), `listing_run_id`. `pending` = a known change not yet applied (legislation.gov.uk lag, shown as a warning, never as text). Two-strike withdrawal reads the last two complete `listing_run_id`s. Index `(tenant_id, source_id, external_id, observed_at DESC)`. No UPDATE or DELETE grant except the erasure of an erased source |
| `document_versions` | `(tenant_id, version_id)` | `doc_id` (composite FK to `documents`), `version_key`, `valid_range daterange NOT NULL` (half-open `[from, to)`, UTC days), `valid_from_basis` (`source` or `observed`: a source with current text only, such as the FCA API, is `observed` and an as-of date before the first observation is refused with "no version history for this source"), `system_range tstzrange NOT NULL DEFAULT tstzrange(clock_timestamp(), NULL)`, `bronze_sha256`, `bronze_uri`, `content_hash`, `parser_version`, `attribution_text` (licence footer text), `scan_passed`, `contract_passed`, `quarantine_reason`, `released_by`, `status` in (`ingesting`, `active`, `superseded`, `revoked`, `withdrawn`, `quarantined`, `known_pending`, `erased`), `created_at`. Unpartitioned |

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- document_versions is NOT partitioned, so the constraint lives on the table itself
ALTER TABLE document_versions ADD CONSTRAINT document_versions_no_overlap
  EXCLUDE USING gist (tenant_id WITH =, doc_id WITH =, valid_range WITH &&)
  WHERE (upper_inf(system_range) AND status NOT IN ('ingesting', 'quarantined', 'erased'));

-- idempotency key: same bytes seen twice is a no-op; ON CONFLICT cannot arbitrate on an EXCLUDE constraint
CREATE UNIQUE INDEX document_versions_idem ON document_versions
  (tenant_id, doc_id, version_key, bronze_sha256) WHERE upper_inf(system_range);
```

- The constraint covers the current belief only (rows with an open `system_range`); historical `system_range` rows are not constrained. Rows still `ingesting` or `quarantined` carry a provisional range and are outside the constraint; the publish transaction closes the previous head, sets the new range and flips the status together (§4.17). Constraint checks bypass RLS, and every key starts with `tenant_id`, so they leak nothing across tenants.
- Same `version_key` with different bytes is a `silent_edit`: the old row's `system_range` is closed and a new row with the same `valid_range` is inserted in one transaction, with an alert. Upserts use the unique index above (https://www.postgresql.org/docs/16/sql-insert.html ).
- `known_pending` marks a provision with a known amendment not yet applied: retrieval is unaffected, the compliance check adds a warning.
- Rows of the source class `law` and Q&A are retired (valid range closed, text kept); rows of `fca_api` and `publisher` are erased physically (§4.19).

### 5.10 Chunk versioning, identity, EXCLUDE per leaf and embedding generations (R4-D3, R4-D13; ADR-027, ADR-035)

- **Range merge at version publish** (inside `reconcile_lineage`, §4.16): for each provision path, the same `chunk_hash` as the previous version extends `valid_range` (no embed call); a changed chunk closes the old row at the new `valid_from` and inserts a new one; a removed provision closes the row. Embeds therefore scale with changed provisions, not versions times provisions.
- **Identity** is `(tenant_id, document_id, provision_path, chunk_index, chunk_hash, valid_from, parser_version, embed_model)`, unique. `valid_from` makes A-B-A text (text A, then B, then A again) two rows with disjoint ranges instead of a unique violation or a wrong extension; `parser_version` makes a replay after a parser fix a re-parse with an atomic swap, not a no-op. `valid_from` is stored and checked equal to `lower(valid_range)`. Vector reuse is by `(tenant_id, chunk_hash, embed_model)`, now a plain index, not a unique constraint.
- **EXCLUDE on `chunks` is per leaf partition, not on the parent.** PostgreSQL 16 cannot declare an exclusion constraint on a partitioned table; it can only be put on each leaf partition (https://www.postgresql.org/docs/16/ddl-partitioning.html , Limitations; PostgreSQL 17 lifts this: https://www.postgresql.org/docs/17/release-17.html ). The constraint therefore goes into the per-tenant partition-creation migration (`migrate --onboard-tenant`, and the PUBLIC partition migration):

```sql
-- executed for every leaf by the partition-creation migration (shape; exact column list fixed in the onboarding ticket)
ALTER TABLE chunks_<tenant> ADD CONSTRAINT chunks_<tenant>_no_overlap
  EXCLUDE USING gist (tenant_id WITH =, document_id WITH =, provision_path WITH =,
                      chunk_index WITH =, kind WITH =, embed_model WITH =, valid_range WITH &&)
  WHERE (upper_inf(system_range));
```

  List partitioning by tenant makes a cross-partition exclusion moot. **L0 test:** every leaf partition of `chunks` (each tenant and PUBLIC) has this constraint; `migrate` also asserts it, like the other partition assertions (§5.3). The swap order inside the publish transaction is: close the old rows' `system_range`, then insert the new ones.
- **Embedding generations are rows, not columns.** `embed_generations(model_id PK, status in (building, validating, active, retired))` is global reference data (no `tenant_id`, written only by migrations); `tenants.active_embed_model` names the generation queries use. A new generation is a second set of `chunks` rows with the new `embed_model` beside the old one (parents copied); the HNSW index is partial per generation (`WHERE kind = 'child' AND embed_model = '<model>'`) and queries inline the model literal from the allow-list (§5.6), so a half-built generation is invisible and a query embedded with the wrong model raises. The old generation is kept for rollback, erased with the chunk (deletion is by `doc_id`, so it hits every generation). Two generations double the HNSW size during the overlap, so the cutover is bounded by the 8 GiB instance (§4.27).
- **E3 spike (open, §10):** build a partition with 30% superseded rows and measure recall@10 and p95 against current-only, under RLS and LIST partitions; behaviour of pgvector iterative scan there is an evidence gap (evidence-r4.md §2.2). Trigger for the partial index `WHERE is_current`: a recall or p95 miss.

### 5.11 Deletion tables (R4-D6; ADR-029, ADR-030)

| Table | Key | Columns (beyond key) and rules |
|---|---|---|
| `deletion_requests` | `(tenant_id, id)` | The queue (no Kafka). `scope` in (`document`, `source`, `advisor`, `tenant`), `subject_ref` (document `doc_key`, `source_id`, or advisor `pseudonym_id`), `reason` in (`erasure`, `takedown`, `source_withdrawal`, `offboarding`, `source_kill`), `requested_by`, `requested_at`, `status` in (`pending`, `running`, `executed`, `windows_open`, `closed`, `failed`), `claimed_at`, `attempts`, `parent_request_id` (the `purge_source` fan-out). Polled with `FOR UPDATE SKIP LOCKED` on a partial index `WHERE status = 'pending'` |
| `erasure_ledger` | `(tenant_id, doc_key, sha256)` | The tombstone, append-only, hashes only, no content. `doc_key` is the salted hash of the document's `doc_key` (salt in Secret Manager); for advisor and tenant scopes it holds `subject:<salted hash>` and `sha256` is the empty string. `request_id`, `scope_type`, `requested_at`, `released_at` and `released_by` (the explicit `release` action for a legitimate re-ingest). Written first, under the document's advisory lock, before any delete. Tenant-scoped, so Firm A's tombstone never blocks Firm B. Exported daily to an append-only GCS object; replayed by `erasure-replay` after any restore |
| `erasure_steps` | `(tenant_id, request_id, store)` | `status`, `executed_at`, `rows_affected`, `probe_result`, `window_closes_at`, `swept_at` (end-of-window re-sweep) |
| `erasure_receipts` | `(tenant_id, request_id, phase)` | `phase` 1 `executed` or 2 `windows_closed`; `receipt jsonb` (per-store results and probes), `hmac` (Cloud KMS key), `gcs_uri`, `issued_at`; the receipt hash is also recorded in the ledger. No receipt claims "erased everywhere" before phase 2 |
| `lineage_edges` | `(tenant_id, id)` | `run_id`, `in_ref`, `out_ref`, `stage`, `parser_version`, `ts`: links bronze sha256, version, chunk hash, embedding generation, cited messages (`retrieval_chunk_ids`) and BigQuery events. The scope resolver for erasure and `purge_source`; never a gate. Own table, OpenLineage-shaped JSON |

Write guards in every sink read `erasure_ledger` with an UNCACHED point read inside the sink's own transaction or write path (no 60 s cache). Lock order for erasure and publish alike: advisory lock, then the tenant `corpus_version` row last (§4.17).

### 5.12 Pseudonyms, reconciliation manifests and tenant flags (R4-D6, R4-D12, R4-D10)

| Table / column | Key | Columns and rules |
|---|---|---|
| `pseudonym_map` | `(tenant_id, advisor_id)` | `pseudonym_id uuid NOT NULL UNIQUE`, random (not derived from `idp_uid` or email). Outbox events, BigQuery rows, Kafka payloads, Langfuse metadata and logs carry `pseudonym_id` only. Erasing an advisor deletes the mapping row at once, so surviving rows in slow stores become unlinkable immediately while physical deletion runs inside the windows. Unlinking is not claimed as erasure |
| `reconciliation_manifests` | `(tenant_id, version_id, hop, parser_version)` | `hop` in (`bronze`, `silver`, `chunks`, `bigquery`), `n_chunks`, `chunk_set_hash` (`sha256(sorted(chunk_hash))`), `computed_at`. Keyed on `parser_version`, so a parser bump is a planned re-baseline. The PUBLIC manifest (document count + `chunk_set_hash` per version) is compared across cells. Findings go to `reconciliation_findings(tenant_id, id, pair, detail, status, opened_at)` |
| `tenants.llm_egress_ack` | n/a | `boolean NOT NULL DEFAULT false`. Must be true before private ingest for the tenant (the `publisher` connector and any firm upload refuse otherwise): private text reaches Anthropic and Voyage (embed and rerank) outside the cell's region (ADR-038). Enabled explicitly for the demo tenants |
| `tenants.cell_id` | n/a | The tenant's home cell; equals the entry in the signed `cells.json`; a request for a tenant whose `cell_id` is another cell never reaches this table (421, §4.24) |

### 5.13 RLS and grants of the new tables

All tenant tables below: `ENABLE` and `FORCE ROW LEVEL SECURITY`; settings come from `principal` as in §5.4; policies call `current_setting('app.x')` without `missing_ok` (fail closed).
- `document_versions`: SELECT `TO fa_app` when `tenant_id = app.tenant_id OR tenant_id = <PUBLIC>` AND a visible `documents` row exists for `(tenant_id, doc_id)` (the `documents` policy supplies tier and jurisdiction); pipeline roles: own tenant only; writes as in §5.3. No INSERT / UPDATE / DELETE policy for `fa_app`.
- `source_registry`, `source_observations`, `lineage_edges`, `reconciliation_manifests`, `reconciliation_findings`: pipeline roles, own tenant; `fa_etl_public` for PUBLIC; no `fa_app` grant.
- `deletion_requests`: INSERT `TO fa_app` when `app.role = 'tenant_admin'` and the tenant matches; `fa_worker` SELECT and UPDATE (`status`, `claimed_at`, `attempts`) on its own non-PUBLIC tenant; `fa_etl_public` INSERT for firm tenants only for the `purge_source` fan-out. `erasure_ledger`: `fa_worker` SELECT and INSERT; no DELETE for anyone; UPDATE of `released_at`, `released_by` only for the operator release command role (set in E12); no `fa_app` grant. `erasure_steps`, `erasure_receipts`: `fa_worker` SELECT, INSERT, UPDATE.
- `pseudonym_map`: INSERT `TO fa_app` with the advisor row (tenant_admin), SELECT for `fa_app` and `fa_worker`, DELETE `TO fa_worker` for erasure.
- `embed_generations`: global; SELECT to every runtime role, written by `fa_owner` migrations.
- The L0 leak matrix gains: new tables cross-tenant read / write, FK probes on `document_versions`, a misrouted token returning 421 with an empty DB query log, every `chunks` leaf carrying the `EXCLUDE` constraint, and the replay test (deleted data does not return after a parser bump and replay).

### 5.14 Per-store retention settings and deletion windows (R4-D6, R4-D9; ADR-029)

| Store | Setting | Value | Window after the erasure step | Evidence |
|---|---|---|---|---|
| Postgres live | explicit ordered DELETE, then `VACUUM` of the affected partitions | n/a | rows immediate; dead tuples and HNSW entries until vacuum; within 24 h of the system running | evidence-r4.md §2.3 |
| Cloud SQL backups | automated backup retention | 7 d; no on-demand backups kept | up to 7 d; ledger replay on restore. PITR log retention days and whether old backups expire while the instance is stopped are UNVERIFIED (§10) | https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/backups |
| GCS data bucket | soft delete policy; versioning; retention lock | `soft_delete_policy` 0; versioning off; never a retention lock | immediate | https://cloud.google.com/storage/docs/soft-delete |
| BigQuery (every dataset, including dbt-created ones) | `max_time_travel_hours` | 48 | within 14 d: 2 d time travel + 7 d fail-safe (fixed, not observable); the batched DML runs hourly on refs older than 30 min (streaming buffer) | https://docs.cloud.google.com/bigquery/docs/time-travel |
| Kafka subject-bearing topics (Confluent Basic) | cleanup policy, `retention.ms`, `segment.ms` | delete (no compaction); 7 d; 1 d (editable, minimum 4 h) | about 8 d, inside the 14 d bound; `retention.ms` maximum on Basic not found | https://docs.confluent.io/cloud/current/topics/manage.html |
| Cloud Logging `_Default` | bucket retention | 7 d; no PII in logs (Kong field whitelist, `pseudonym_id` only) | 7 d | evidence-r4.md §2.3 |
| Langfuse Cloud | trace delete by `messages.trace_id` | no setting; nightly cleanup of traces older than 30 d | provider best effort ("usually within 15 minutes"), stated as provider-bound; retry, alert at 24 h | evidence-r4.md §2.3 |
| Valkey | counters only | n/a | n/a | §4.6 |
| Anthropic, Voyage | provider terms | n/a | outside the promise | evidence-r4.md §2.5 |

Promise (R4-D9): live stores within 24 h of the system running (in demo-on-demand the erasure job runs first at every start); analytics and streams (BigQuery incl. 48 h time travel + 7 d fail-safe, Kafka) within 14 d; backups within 7 d plus ledger replay on restore. BigQuery fail-safe and Cloud SQL PITR logs are documented windows, not observable: the canary measures only observable stores and runs at each demo start (§4.23).
