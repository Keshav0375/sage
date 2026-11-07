EVIDENCE

Track B (data engineering), research round 4, project finadvisor. Read 2026-11-01 and 2026-11-02.
Method: page-reader leaves fetched through WebFetch. WebFetch passes pages through a small summarizing model, so every quote is "as relayed", not byte-verified. Extracts are in /Users/keshav/Projects/sage/context/.runtime/research/finadvisor/r4/pages/. Items not found are marked UNVERIFIED. Not covered by any leaf (budget): dbt tests/contracts, Pandera, Great Expectations, pgvector README, PG18 temporal syntax. These are listed under Gaps, with no facts from memory.

## Confirms

Langfuse
- Trace deletion API exists, single and batch, cascades to scores and observations — "DELETE /api/public/traces/{traceId}" and batch "DELETE /api/public/traces" with {"traceIds":[...]}; "all trace deletions will delete related entities like scores and observations across all data storages." — https://langfuse.com/docs/administration/data-deletion (no page date, read 2026-11-01)
- Tracing-data deletion is asynchronous, about 15 min — "Most deletions in Langfuse happen instantly, but the deletion of tracing data does not." / "Usually, trace data is deleted from our system within 15 minutes of the delete call." — same URL (read 2026-11-01)
- Project deletion is async and can take days — "immediately revokes all API keys and schedules the project for deletion"; "For very large projects, deletion can take multiple days." — same URL
- Deletion is not plan-gated; sessions have no delete endpoint (look up trace IDs, then batch delete) — session deletion "Available" on Hobby, Core, Pro and Enterprise — same URL
- Project data retention setting is Pro/Enterprise only, min 3 days — "we accept a number of days with a minimum of 3 days." Deleted nightly: "traces, observations, scores, and media assets that are older than the configured retention period." Hobby shows "--" for retention management — https://langfuse.com/docs/administration/data-retention and https://langfuse.com/pricing (no page date, read 2026-11-01)
- Hobby limits — "50k units / month included"; "30 days" data access; "2 users"; projects "Unlimited"; Core $29 (90 days access), Pro $199 and Enterprise $2,499 (3 years access); older data "is still stored and becomes accessible again when you upgrade." — https://langfuse.com/pricing (read 2026-11-01)

Confluent Cloud
- Schema Registry hard delete is two-step on Cloud — "You must first soft delete the schema, then hard-delete it." / "support hard delete of a schema with the use of the query string, `?permanent=true`." / "A hard delete removes all metadata, including schema IDs." Soft delete: "the underlying schema ID would still be available for any lookup." — https://docs.confluent.io/cloud/current/sr/schemas-delete-cc.html (no page date, read 2026-11-01)
- Client-side field-level encryption with Google Cloud KMS KEKs is supported, needs Stream Governance Advanced — "Stream Governance Advanced package must be enabled."; KEKs held in external KMS encrypt DEKs which encrypt fields; Google Cloud KMS supported; DEK Registry limit 10,000 DEKs — Confluent CSFLE docs and stream-governance/packages (updated Oct 29, 2026; manage-keys page updated Oct 23, 2026)
- Losing the KEK makes data unreadable (the docs never say "crypto-shredding") — "If your Key Encryption Key (KEK) is lost or compromised, all DEKs encrypted with that KEK become inaccessible." and "without KEK access from KMS the data can't be decrypted" — same CSFLE pages
- Basic cluster limits — "Basic supports 1 to 50 eCKU"; ingress 250 MBps, egress 750 MBps, 1,500 partitions (pre-replication), 1,500 compactable partitions, 8 MB message size, 5 TB per partition (Basic only; other types unlimited), uptime SLA 99.5% — https://docs.confluent.io/cloud/current/clusters/cluster-types.html (Last updated Oct 30, 2026, read 2026-11-01)
- Basic pricing (summarized from the pricing page, not raw) — "First eCKU free, then $0.14" per eCKU-hour; "$0.05" per GB data in/out; "$0.08" per GB-month storage — https://www.confluent.io/confluent-cloud/pricing (no date shown, read 2026-11-01). The billing overview page has no rates: "For current rates, see Confluent Cloud Pricing."
- Infinite retention is available as a topic setting — "You can create a topic with Infinite Storage by specifying -1 for `retention.ms`." — https://docs.confluent.io/cloud/current/topics/overview.html (Last updated Oct 22, 2026). No Basic restriction found in the text read (see Gaps).

Cloud Logging
- Retention — "the default is `30 days`"; custom retention "between 1 day and 3650 days."; _Required bucket "400 days," fixed ("You can't change the retention period of the `_Required` log bucket."); "Locking a log bucket is irreversible." — https://cloud.google.com/logging/docs/buckets and /logging/quotas (Last updated 2026-10-30 UTC, read 2026-11-01)
- Bucket deletion is delayed 7 days — "The bucket, including all the logs in it, is deleted after 7 days." — /logging/docs/buckets
- Exclusion filters drop entries at routing, not at write — "If the log entry matches the inclusion filter and at least one exclusion filter, then it isn't routed." "Exclusion filters are applied after log entries are received by the Logging API." They don't reduce entries.write quota — /logging/docs/routing/overview
- CMEK key removal has up to 1 hour lag — "If you remove Logging's access to a key, then it can take up to one hour for the change to take effect." (org/folder CMEK page; bucket-level CMEK page not found) — /logging/docs/routing/managed-encryption

GCS
- Soft delete is on by default, 7 days, range 7 to 90, 0 disables — "Soft delete is enabled by default for all buckets that support it, with a default retention duration of 7 days."; "you can customize the retention duration between 7 days and 90 days."; "To disable soft delete, you set the retention duration to 0." — https://cloud.google.com/storage/docs/soft-delete (Last updated 2026-10-30 UTC, read 2026-11-01)
- Soft-deleted objects can't be purged early — "During this time, the object or bucket can't be permanently deleted and can be restored." No early-purge method on the page.
- Versioning keeps noncurrent versions until you delete them by generation or lifecycle — "Cloud Storage retains a noncurrent object version each time you replace or delete a live object version"; "You delete a noncurrent version of an object by including the generation number in the deletion request" — /storage/docs/object-versioning
- Retention lock is irreversible and blocks erasure — "Once you lock a policy, you cannot remove it or reduce the retention period it has." / "You cannot delete a bucket with a locked policy unless every object in the bucket has met the retention period." Max 100 years — /storage/docs/bucket-lock
- Lifecycle is asynchronous — "Cloud Storage performs an action asynchronously"; "Your applications shouldn't rely on lifecycle actions occurring within a certain amount of time" — /storage/docs/lifecycle

Cloud SQL
- Destroyed CMEK key version is unrecoverable — "Once you destroy a key version that is associated with a Cloud SQL instance, Google can't get the data back." / "Enhanced backups encrypted using a key version that has been destroyed become permanently unrestorable." Disabled key: "Cloud SQL suspends the instance." and resumes automatically after re-enable (up to 10 min) — https://cloud.google.com/sql/docs/postgres/cmek (Last updated 2026-10-27 UTC, read 2026-11-01)
- PostgreSQL 18 is supported and listed "(default)" (18.6, regular support from Sept 25, 2025). Majors listed: 18, 17, 16, 15, 14, 13, 12, 11, 10, 9.6 — https://cloud.google.com/sql/docs/postgres/db-versions (Last updated 2026-10-26 UTC). The page does not label it GA or preview.
- pgvector >= 0.8 is available — "PostgreSQL versions 13 and later support version 0.8.5" (PG12 up to 0.7.4) — https://cloud.google.com/sql/docs/postgres/extensions (Last updated 2026-10-26 UTC). Prose, not a per-major table.
- btree_gist on PG18 is v1.8 (PG15/16/17 use 1.7) — extensions page. This is the extension needed for exclusion constraints mixing scalar equality with range overlap.

Cloud KMS
- Default scheduled destruction is 30 days, configurable only at key creation, min 24 hours, max 120 days — "By default, keys in Cloud KMS spend 30 days in the Scheduled for destruction state"; "The duration is only configurable during key creation."; "The minimum duration is 24 hours for all keys, except for import-only keys which have a minimum duration of 0."; "The maximum duration is 120 days." — https://cloud.google.com/kms/docs/key-states and /kms/docs/destroy-restore (Last updated 2026-10-27 UTC, read 2026-11-01)
- Destruction is crypto-shredding in Google's own words — "After a key is destroyed, data that was encrypted with the key version can't be decrypted." Data "is considered crypto-shredded." — /kms/docs/destroy-restore
- No quota on key count — "There are no quotas on the number of key rings, keys, key versions"; read/write default 600/100 TPM per project after Feb 16, 2026 (token-based metrics) — https://cloud.google.com/kms/docs/quotas (Last updated 2026-10-27 UTC)
- Pricing, from a search-result summary only (the pricing page fetch returned a title) — software key about $0.06 per active key version per month; "A key version is active if it is in any of these states: Enabled, Disabled, Scheduled for destruction"; "Key versions in any state other than destroyed incur costs." Operations $0.03 per 10,000 — https://cloud.google.com/kms/pricing (search summary says page dated March 17, 2025; UNVERIFIED against live page)

BigQuery
- Mutating DML is serialized per table — "BigQuery runs up to 2 of them concurrently, after which up to 20 are queued as `PENDING`."; "Queued mutating DML statements share a per-table queue with maximum length 20." No DELETE-specific quota stated — https://cloud.google.com/bigquery/docs/data-manipulation-language (Last updated 2026-10-28 UTC, read 2026-11-02)
- Recent streamed writes are special — "The recent writes are those that occurred within the last 30 minutes."; "Running mutating DML statements within a multi-statement transaction against recently streamed data is unsupported." — /bigquery/docs/write-api (no date)
- AEAD keysets are wrapped by a KMS key in the same region — "Creates a new keyset and encrypts it with a Cloud KMS key."; "The Cloud KMS key must reside in the same Cloud region where this function is executed."; "A user must be granted permission to both the table and the encryption key to read data in cleartext." — /bigquery/docs/reference/standard-sql/aead_encryption_functions and /bigquery/docs/column-key-encrypt (Last updated 2026-10-27 UTC)

Dagster (latest 1.13.28 core / 0.29.28 libraries; dagster 1.13.28 uploaded to PyPI 2026-10-30; CHANGES.md has no date)
- Blocking asset checks work as designed — "By default, if a parent's asset check fails during a run, the run will continue and downstream assets will be materialized." Fix: "set the `blocking` argument to `True` in the `@asset_check` decorator" so the downstream asset "won't be materialized." — https://dagster.io/docs/guides/test/asset-checks (docs.dagster.io 308-redirects here, read 2026-11-02). Blocking applies within a run only.
- Single-run backfills exist — "Dagster supports backfills that execute as a single run that covers a range of partitions." (backfill_policy single_run) — https://dagster.io/docs/guides/build/partitions-and-backfills/backfilling-data
- Sensor dedupe and cursor — "Dagster will skip processing requests with previously used run keys, ensuring that duplicate runs won't be created."; cursor "to optimize sensor performance"; minimum_interval_seconds "the minimum number of seconds that will elapse between sensor evaluations." — https://dagster.io/docs/guides/automate/sensors
- dagster-openlineage exists, young and active — latest 0.2.1 released 2026-05-22 (0.2.0 2026-05-19, 0.1.0 2025-12-23); "Asset-centric OpenLineage emission for Dagster."; no deprecation notice; maintainer elementl — https://pypi.org/project/dagster-openlineage/ (PyPI JSON, read 2026-11-02)
- Declarative Automation is a documented, unlabelled (not beta, not deprecated) framework — "Declarative Automation is a framework that uses information about the status of your assets"; requires enabling the default automation condition sensor — https://dagster.io/docs/guides/automate/declarative-automation

## Contradicts

- Langfuse Hobby cannot configure data retention and has no stated retention window; the only stated window is 30 days of data access. Any design that relies on "Langfuse retention TTL" for erasure needs Pro ($199) — "Hobby shows '--' for retention management"; retention is "a separate, opt-in feature on Pro and Enterprise." — https://langfuse.com/pricing (read 2026-11-01). Per-trace delete API is the only Hobby erasure path.
- Cloud Logging: no documented way to delete an individual log entry — "Logs can't be recovered after the applicable retention period ends." is the closest statement; no delete-entry API is documented. Erasure options are bucket retention expiry, bucket delete (7-day delay) or never logging the data (exclusion filter / redaction before write). — /logging/docs/buckets (read 2026-11-01). Treat per-entry deletion as unavailable (docs silent, not an explicit prohibition).
- Cloud SQL: no documented per-row purge from backups or PITR logs; docs silent. PITR retention days not found. Only key-destruction makes enhanced backups unrestorable. — /sql/docs/postgres/backup-recovery/pitr (Last updated 2026-10-26 UTC)
- Confluent Basic: cluster-level settings cannot be changed — "You cannot edit cluster settings on Basic, Standard, Enterprise, and Freight clusters in Confluent Cloud." The broker-level compaction setting (log.cleaner.max.compaction.lag.ms, min 21600000 ms) is in a table that "apply only to Dedicated clusters". Do not assume broker-level compaction lag tuning on Basic. — https://docs.confluent.io/cloud/current/clusters/broker-config.html (Last updated Oct 23, 2026)
- BigQuery fine-grained DML tables cannot drop single partitions — "A table enabled with fine-grained DML can't have partitions individually deleted or overwritten." — DML page. And "Enabling fine-grained DML won't reduce the amount of scanned bytes of the DML statement itself."
- BigQuery AEAD pages contain no statement on crypto-shredding or deleting a keyset/KEK. Crypto-shredding with AEAD is a design inference (delete the wrapped-keyset row or destroy the KMS key), not a documented pattern. KMS destroy-restore does call destroyed data "crypto-shredded" for KMS itself.

## Limits

- Langfuse deletion: no numeric rate limit or max batch — "we rate limit how many deletions we process at any point in time." Example script batches 1,000 IDs by its own choice. Observations API v2 read window is 30 days on Hobby, 90 on Core, which limits the session-to-trace-ID lookup — data-deletion page (read 2026-11-01)
- Confluent Basic: 5 TB per partition; 1,500 partitions; 250 MBps in / 750 MBps out; "Basic clusters are limited to one task per connector" (250 connectors); "Basic clusters do not support RBAC roles for resources within the Kafka cluster." — cluster-types page (Oct 30, 2026)
- Confluent Schema Registry: Essentials "included count of 100" and "Essentials doesn't enforce a cap" (overage charged); Advanced "default cap matches the included count of 20,000", "starting at $1/hour". Per-schema overage rate not found. DEK Registry 10,000 DEKs — stream-governance/packages (updated Oct 29, 2026)
- Cloud Logging: quotas page lists retention costs beyond default (effective April 1, 2023); per-GiB figures not found (pricing page returned only a title).
- KMS: key versions per key and keys per project are unlimited; request quota 600 TPM read, 100 TPM write per project (relevant to per-subject key unwrap fan-out) — /kms/quotas
- BigQuery: 2 concurrent plus 20 queued mutating DML per table — a per-subject erasure design must batch deletes (UNVERIFIED how many rows per statement; no row cap found).
- Langfuse project-delete can take multiple days; org delete errors while a project deletion is processing.

## Vendor recommends

- Langfuse: delete in batches through the batch trace endpoint and verify by re-querying (no confirmation is returned) — data-deletion page.
- GCS: use object versioning plus a lifecycle rule to remove noncurrent versions; lifecycle runs asynchronously, so do not rely on timing — /storage/docs/object-versioning, /storage/docs/lifecycle.
- Google KMS: scheduled destruction is the recommended safety net (restore possible while "Scheduled for destruction", state can be restored to disabled) — /kms/docs/key-states.
- Dagster: set `blocking=True` on checks that must gate downstream assets; use `run_key` for sensor idempotency; use cursors for sensor efficiency; use single-run backfill policies for large partition ranges — Dagster pages above.
- Confluent: hard delete in Schema Registry is soft-then-permanent only — schemas-delete-cc page.

## Changes

- Cloud SQL default PostgreSQL is now 18 (18.6) — db-versions page, Last updated 2026-10-26 UTC. PG18 is available, so native temporal constraints are potentially usable. Syntax and limits not verified (see Gaps).
- KMS API quotas moved to token-based metrics after Feb 16, 2026: read 600 TPM, write 100 TPM (from 300 QPM / 60 QPM) — /kms/quotas.
- BigQuery: fine-grained DML exists as a table option and changes partition-delete behaviour (see Contradicts) — DML page, 2026-10-28.
- dagster-openlineage 0.2.1 (May 2026): "`OpenLineageEventListener` is removed"; `include_asset_events` default changes in v0.3 — PyPI page. Expect breaking changes before 1.0.
- Confluent docs now list "Freight" alongside Basic/Standard/Enterprise cluster types — broker-config page.

Improvements:
- Do not rely on Langfuse Hobby for retention-based erasure. Either upgrade to Pro, or run a deletion job against the batch trace endpoint, tracked by subject-to-trace-ID mapping stored on our side (Hobby read window 30 days means lookup by session after 30 days will not work through the v2 API; store trace IDs at write time).
- Keep personal data out of Cloud Logging rather than planning to delete it later (no per-entry delete). Use short retention (1 to 30 days) on any bucket that could hold subject data, and exclusion filters for known fields.
- Set GCS soft delete to 0 or the 7-day minimum on buckets that hold erasable data, and count the 7 days as the erasure latency; add lifecycle rules for noncurrent versions. Do not use retention lock on subject-data buckets (irreversible).
- Per-tenant or per-subject keys in Cloud KMS: no key-count quota and about $0.06 per active version per month (UNVERIFIED rate), so per-subject keys cost about $0.72 per subject per year; scheduled destruction (min 24 hours, default 30 days) is the erasure latency. Note "scheduled for destruction" versions still bill and still count as active.
- Treat crypto-shredding for BigQuery as our own design: AEAD keyset wrapped by a KMS key, with the key destroyed on erasure. The docs do not describe it; test that decryption fails after key destruction before relying on it.
- Batch BigQuery erasure DML (2 concurrent, 20 queued per table) and avoid DML on rows streamed in the last 30 minutes.
- Run a Cloud SQL test restore after CMEK key destruction in a scratch instance; docs only state enhanced backups become unrestorable, nothing on standard backups, replicas, PITR.
- Confluent Basic: confirm compaction and topic-level `max.compaction.lag.ms`/`delete.retention.ms` with a live test topic before designing tombstone-based erasure; docs found no Basic statement.
- Dagster: mark erasure and PII-gate checks `blocking=True`; remember blocking works only within a run, so a separate backfill run will not be stopped by a failure from another run.

Gaps:
- UNVERIFIED: whether cleanup.policy=compact is allowed on Basic. Only indirect evidence ("Compactable partitions: 1,500", "5 TB per partition for compacted topics").
- UNVERIFIED: Confluent Cloud topic-level configs (max.compaction.lag.ms, min.compaction.lag.ms, delete.retention.ms, segment.ms) editability and ranges on Basic. The Cloud config reference page was not found (leaf got the landing page). Only Confluent Platform defaults were seen: delete.retention.ms default 1 day, retention.ms default 7d, max.compaction.lag.ms [1,...] (Platform topic-configs page, Last updated May 29, 2026); these are Platform, not Cloud.
- UNVERIFIED: max retention.ms on Basic, and whether -1 (infinite) is allowed on Basic.
- UNVERIFIED: Cloud SQL PITR retention days (page only mentions `log-retention-days` for deleted instances); standard backup/replica behaviour after key destruction.
- UNVERIFIED: Cloud Logging bucket-level CMEK behaviour on key destruction; Cloud Logging pricing per GiB; per-entry deletion (docs silent).
- UNVERIFIED: GCS CMEK key destruction effect (leaf read 100k of 154k chars of the CMEK page, no passage found); lifecycle conditions daysSinceNoncurrentTime / numNewerVersions not seen; lifecycle latency (summary said up to 24 h for config changes, paraphrase).
- UNVERIFIED: KMS pricing (search-summary only, dated March 2025 per that summary).
- UNVERIFIED: whether DML can modify rows in the last-30-minutes window. write-api sentence was truncated; DML page text suggests not, exact sentence not captured. BigQuery DELETE bytes-processed formula and DROP-partition comparison not found. Time travel interaction not covered here (prior-art file covers windows).
- UNVERIFIED: PG18 temporal constraints (WITHOUT OVERLAPS, PERIOD in FK) syntax and limits. The PG18 constraints page fetch reported no temporal content; sql-createtable.html not read. Only the facts that PG18 is on Cloud SQL and btree_gist 1.8 ships. PG16 range type + EXCLUDE USING gist: only the generic exclusion-constraint quote "Exclusion constraints ensure that if any two rows are compared on the specified columns or expressions using the specified operators, at least one of these operator comparisons will return false or null." (PG 18.6 docs, 5.5.6) with example EXCLUDE USING gist (c WITH &&).
- UNVERIFIED: pgvector iterative scan (hnsw.iterative_scan, hnsw.max_scan_tuples, ivfflat.iterative_scan), filtering advice and partial-index/partitioning guidance. README never fetched; the only pgvector fact is the Cloud SQL version (0.8.5 on PG13+). Whether iterative scans work under RLS and LIST partitions is not answered.
- UNVERIFIED: Dagster concurrency limits/pools during backfills; whether schedules/sensors keep running during a backfill; relationship of Declarative Automation to auto-materialize (page silent); observable source assets in sensors.
- NOT COVERED (no leaf budget): dbt tests, model contracts and model versions; Pandera with Polars/pandas; Great Expectations vs. fit for Dagster+dbt; dbt-to-OpenLineage. No facts given; carry forward as open.
- Caveat on all quotes: WebFetch returned summarized text; quotes are as relayed. The Langfuse pages show no date.
- The Langfuse, Confluent and GCS pages' load-bearing quotes were not re-checked against the raw page; they are marked in leaf extract files with the same caveat.
