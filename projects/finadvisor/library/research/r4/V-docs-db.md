EVIDENCE (round 4, DB docs). Read 2026-11-07. Pages read directly with WebFetch (no leaf spawned); quotes are from the fetch extractor, not re-checked against raw page text. No page showed a last-updated date unless stated.

## Confirms
- btree_gist supported on Cloud SQL PG16 — "PostgreSQL 15, 16, and 17 use version 1.7." — https://docs.cloud.google.com/sql/docs/postgres/extensions (read 2026-11-07)
- pgvector on PG16 is 0.8.5 (>= 0.8, iterative scan is a 0.8.0 feature; the Cloud SQL page does not mention iterative scan itself -> NOT FOUND) — "PostgreSQL versions 13 and later support version 0.8.5" — same URL
- PG16: no exclusion constraint on the partitioned parent; allowed per leaf — "There is no way to create an exclusion constraint spanning the whole partitioned table. It is only possible to put such a constraint on each leaf partition individually." — https://www.postgresql.org/docs/16/ddl-partitioning.html (v16, read 2026-11-07)
- PARTITION OF inherits indexes, CHECK, NOT NULL, not exclusion constraints — "Create an index on the key column(s)... This automatically creates a matching index on each partition, and any partitions you create or attach later will also have such an index." and "Both CHECK and NOT NULL constraints of a partitioned table are always inherited by all its partitions." Exclusion is parent-impossible, so nothing to inherit; each leaf needs its own EXCLUDE (docs say "only possible to put such a constraint on each leaf partition individually"). Same URL.
- BigQuery dataset max_time_travel_hours — "The max_time_travel_hours value must be an integer expressed in multiples of 24" "(48, 72, 96, 120, 144, 168) between 48 (2 days) and 168 (7 days)." — https://docs.cloud.google.com/bigquery/docs/updating-datasets (read 2026-11-07). 48 is valid.
- Default for new datasets 7 days — "covers the past seven days by default." — https://docs.cloud.google.com/bigquery/docs/time-travel
- Project/org default exists — default_max_time_travel_hours: "The default time travel window in hours for new datasets." Must be 48 to 168 and divisible by 24; affects new datasets only. Set via `ALTER PROJECT ... SET OPTIONS (`region-REGION.default_max_time_travel_hours` = 48)` (page shows the pattern with default_kms_key_name; not this exact statement for time travel) — https://docs.cloud.google.com/bigquery/docs/default-configuration
- Cloud SQL PITR log retention — "from 1-35 for Cloud SQL Enterprise Plus edition, or 1-7 for Cloud SQL Enterprise edition." Defaults: Enterprise 7 days, Enterprise Plus 14 days — https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/configure-pitr
- Stopped instance data — "The instance data is unaffected, and charges for storage and IP addresses continue to apply." — https://docs.cloud.google.com/sql/docs/postgres/start-stop-restart-instance

## Contradicts
- None of the stated decisions contradicted. Note: ADR/overview should not assume 7-day window is only a 7 vs 48h choice; default is 168h, so 48h is an explicit opt-down.
- Backup retention docs are internally inconsistent on units — range "from 1 to 365" (count); "retention can range from 1 day to 10 years" (by backup option); troubleshooting "from seven to 30 days". — https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/backups . Retention 7 is inside every stated range.

## Limits
- time travel 48-168h, multiples of 24; fail-safe fixed — "The fail-safe period isn't configurable and can't be extended." (7 days beyond the window) — time-travel page. Physical billing bills time travel + fail-safe bytes separately; "These savings don't apply when using the logical storage billing model."
- Automated backup count 1-365; deleted instance: "Cloud SQL retains the backups of deleted instances for four days." (for IP restore) and "Automated backups are deleted on a rolling basis, one backup per day, after the instance is deleted." — backups page.
- PITR log retention 1-7 (Enterprise), 1-35 (Plus); PITR "always creates a new instance".

## Vendor recommends
- Set project-level default for new datasets via DDL (default_max_time_travel_hours) — "To specify the project-level default time travel window, you can use data definition language (DDL) statements." — time-travel page.

## Changes
- Cloud SQL PG16 lifecycle — "Cloud SQL regular support start: June 7, 2024; extended support start: February 1, 2029; deprecation date: February 1, 2032" (extractor listing for the PG16 row; "Current minor version 16.15") — https://docs.cloud.google.com/sql/docs/postgres/db-versions . Community EOL date: NOT FOUND on that page. Extended support is charged ("Extended support lets you continue running your Cloud SQL instances for three years"). PG16 is safe through 2027 and 2028 on regular support per this table.
- Docs domain moved cloud.google.com -> docs.cloud.google.com (301).

## NOT FOUND
- Whether automated backup retention/expiry continues while instance is STOPPED (activation policy NEVER): backups page, PITR page, start-stop page all silent. Search result: no doc statement either way. Needs a test on a non-prod instance.
- PITR log retention behavior while stopped: silent.
- dbt-bigquery setting dataset options (max_time_travel_hours): bigquery-configs page (Last updated Nov 4, 2026) does not document it — "None of max_time_travel_hours or storage_billing_model appears on the page." Only grant_access_to for datasets. Use the project default instead; dbt-bigquery source not checked.
- Iterative scan mention for pgvector on the Cloud SQL page; CREATE SCHEMA option for max_time_travel_hours (updating-datasets page silent).

Improvements: (1) Set `default_max_time_travel_hours=48` at project (per-region) level via ALTER PROJECT so dbt-created datasets inherit it; keep ALTER SCHEMA as a bootstrap fallback for existing datasets. (2) Add an explicit EXCLUDE on each leaf partition (migration template), since parent cannot hold it; consider whether partitioning is needed at all. (3) Verify pgvector iterative scan with `SHOW hnsw.iterative_scan` on the instance; docs only give version 0.8.5. (4) Test stopped-instance backup behavior before relying on it; budget a start window for backups/PITR.
Gaps: stopped-instance backup/PITR behavior; PG16 community EOL date; dbt dataset options; precise ALTER PROJECT example for time travel.
