# Cloud SQL for PostgreSQL extract (fetched 2026-11-01)
Note: all 4 URLs 301-redirect cloud.google.com -> docs.cloud.google.com (followed). Quotes via WebFetch summarizer (small model), not raw page text.

## Q1 PITR retention range / selective purge
Source: https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/pitr (Last updated 2026-10-26 UTC)
- Retention range (days): NOT FOUND on this page. Only mention: "`log-retention-days` for the deleted instance are stored with the retained backups"
- Selective purge of a row from logs/backups: NOT FOUND (page covers instance-level PITR, clones, restores only).

## Q2 CMEK disabled/destroyed key
Source: https://docs.cloud.google.com/sql/docs/postgres/cmek (Last updated 2026-10-27 UTC)
- Disabled: if Cloud SQL can't access the key, "Cloud SQL suspends the instance." Re-enabling: "Cloud SQL automatically resumes the instance." (up to 10 minutes)
- Disabled, enhanced backups: "that backup can't be restored unless the key is re-enabled." Standard backups: not stated.
- Destroyed: "Once you destroy a key version that is associated with a Cloud SQL instance, Google can't get the data back."
- Destroyed, backups: "Enhanced backups encrypted using a key version that has been destroyed become permanently unrestorable." Destroying the key version used to create the instance also destroys backups created from it.
- Replicas/PITR: NOT FOUND.

## Q3 Supported versions
Source: https://docs.cloud.google.com/sql/docs/postgres/db-versions (Last updated 2026-10-26 UTC)
Table (major | minor | regular support start | extended support start | deprecation):
- PG 18 (default) | 18.6 | Sept 25, 2025 | - | -
- PG 17 | 17.11 | Oct 22, 2024 | Feb 1, 2030 | Feb 1, 2033
- PG 16 | 16.15 | Jun 7, 2024 | Feb 1, 2029 | Feb 1, 2032
- PG 15 | 15.19 | May 24, 2023 | Feb 1, 2028 | Feb 1, 2031
- PG 14 | 14.24 | Nov 11, 2021 | Feb 1, 2027 | Feb 1, 2030
- PG 13 | 13.23 | Nov 5, 2020 | Feb 1, 2026 | Feb 1, 2029
- PG 12 | 12.22 | May 21, 2020 | Feb 1, 2025* | Feb 1, 2028
- PG 11, 10, 9.6 | 11.22/10.23/9.6.24 | - | Feb 1, 2025* | Feb 1, 2028
*"Starting on May 1, 2025, all instances running on major versions that have reached end of life (EOL) will be charged for extended support."
PG 18 is listed as default; page does not label it GA/preview.

## Q4 pgvector
Source: https://docs.cloud.google.com/sql/docs/postgres/extensions (Last updated 2026-10-26 UTC)
No per-major table; prose: "PostgreSQL versions 13 and later support version 0.8.5," "PostgreSQL version 12 supports up to version 0.7.4," "and PostgreSQL version 11 supports up to version 0.5.1." (>=0.8.0 available on PG13+, incl. 18.) No version for 9.6/10.

## Q5 btree_gist / temporal
- btree_gist: "PostgreSQL 9.6 uses version 1.2. PostgreSQL 10, 11, 12, and 13 use version 1.5." "PostgreSQL 14 uses version 1.6. PostgreSQL 15, 16, and 17 use version 1.7. PostgreSQL 18 uses version 1.8."
- temporal_tables extension: "Provides support for temporal tables." "A temporal table records the period of time when a row is valid from a database perspective." Version 1.2.2. No other temporal/period feature rows.
