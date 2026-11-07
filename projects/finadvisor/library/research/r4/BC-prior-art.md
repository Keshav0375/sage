# EVIDENCE: r4 Tracks B and C prior art (FinAdvisor)

Author: reference-scout. Date of research: 2026-11-01. Sources older than 3 years (before 2023-11-01) are marked [OLD].
Method note: Exa hit its free rate limit mid-run, so later topics used WebSearch/WebFetch. Quotes below came from fetch results; items I could not verify from a primary page are marked UNVERIFIED. I did not use page-reader leaves (pages were short fetches).

---------------------------------------------------------------------
## Topic 1. Change capture from external document sources

### 1.1 Google Drive Changes API (token-based change feed)
- Source: https://developers.google.com/workspace/drive/api/guides/manage-changes (Google, fetched 2026-11-01, page undated).
- Problem/scale: no scale number published on the page.
- Architecture: take `changes.getStartPageToken`, call `changes.list`, follow `nextPageToken`, then "the client application should store the `newStartPageToken` in the response for future use." Entries "are in chronological order (the oldest changes appear first)". `changes.watch` push notifications "don't contain details about the changes", so you poll the feed afterward. `includeRemoved` controls whether removed items show.
- Later change/lessons: page is silent on watch-channel expiry (read the notifications guide). No stronger ordering guarantee than chronological.
- Vs ours: the watermark is an opaque server-issued token, not a timestamp. Push is a hint, the feed is the truth. Take: store the token in the same transaction as the ingest, and treat webhooks as "poll now" only.

### 1.2 Airbyte incremental sync (cursor + primary key)
- Source: https://docs.airbyte.com/platform/using-airbyte/core-concepts/sync-modes/incremental-append-deduped (Airbyte docs, fetched 2026-11-01, undated).
- Architecture: "A `cursor` is the value used to track whether a record should be replicated in an incremental sync" (e.g. `updated_at`); dedup keeps the latest row per primary key by cursor. Deletes arrive only from sources that emit delete events, such as CDC sources (the page does not say hard deletes are detected otherwise).
- Lessons (fetch summary, not a direct quote): at-least-once delivery, so sources may resend; a record modified without its cursor field updating can be missed; coarse cursor granularity (day) makes resends likely.
- Vs ours: cursor sync cannot see hard deletes and misses silent edits. For document sources without a feed we need periodic full-listing diff (hash/ETag compare) as the backstop, plus an overlap window on the watermark.
- Gap: I did not retrieve Fivetran docs.

### 1.3 Notion Page State (hash-based change detection before re-embedding)
- Source: https://www.notion.com/blog/two-years-of-vector-search-at-notion (Notion, 2026-02-19; Gondi, Liu, Louie, Lund, Sager).
- Scale as published: "multi billion object workload"; sub-minute latency on the online path (Kafka consumers) plus offline Spark batch path.
- Architecture: original code "re-chunk, re-embed, and re-upload all of the spans in that page - even if only a single character changed." Fix (per secondary summary https://www.gend.co/blog/notion-vector-search-10x-90-cost, undated, UNVERIFIED against Notion text): two 64-bit xxHash values per span (text, metadata), cached in DynamoDB; metadata-only change (e.g. permissions) skips embedding; Notion reports 70% reduction in data volume (via that summary).
- Vs ours: matches ADR-022 (ACL change = metadata patch). Take: store a content hash per chunk and per source version so a re-delivered or out-of-order change is a no-op.

### 1.4 Legal publisher: legislation.gov.uk (UK)
- Source: https://www.legislation.gov.uk/changes and https://www.legislation.gov.uk/understanding-legislation (UK National Archives; via WebSearch summary 2026-11-01, pages not fetched directly).
- Facts reported: effects are listed as "applied" or "unapplied" by the editorial team; "unapplied" effects shown beside provisions; applying effects takes "around four to eight weeks" per a community editorial wiki (http://community.legislation.gov.uk/mediawiki/index.php?title=Revising_Legislation/Introduction_to_Revising_Legislation, undated); secondary legislation generally not revised; point-in-time only after base date 1 Feb 1991 for secondary legislation.
- Vs ours: closest legal analogue for "late changes": the amending instrument exists (known) before the consolidated text is updated. Take: model "known change, not yet applied" as a first-class state with a banner, rather than hiding the lag.
- No close match found for commercial regulatory data providers (Westlaw, Lexis, Thomson Reuters Regulatory Intelligence): none published engineering write-ups I could find.

---------------------------------------------------------------------
## Topic 2. Bitemporal versioning, "as of" queries, derived data

### 2.1 XTDB
- Source: https://docs.xtdb.com/concepts/key-concepts.html (XTDB docs, fetched 2026-11-01, no date or version on page).
- Architecture: "'System time' represents the audit history of all changes to records." "'Valid time' is a user-managed dimension." Updates are non-destructive, new rows beside old. Default query context is "as of now". Valid time "can support out-of-order updates and backfilling" (fetch summary). `_valid_from`/`_valid_to` are closed-open; a built-in WITHOUT OVERLAPS constraint prevents overlap. System time can be set on import from legacy bitemporal systems.
- Vs ours: the model fits (valid time = effective date of the regulation text, system time = when we ingested it). We would not adopt XTDB (new datastore) on a $100-200/month demo.
- Note: non-destructive history conflicts with erasure (Topic 3). Take: keep bitemporal rows only for source documents that are firm-owned and erasable by tenant delete, and design deletion to remove all versions.

### 2.2 PostgreSQL 18 temporal constraints
- Source: https://www.postgresql.org/docs/18/release-18.html (PostgreSQL, released 2025-09-25). Quote: "Allow the specification of non-overlapping PRIMARY KEY, UNIQUE, and foreign key constraints ... specified by `WITHOUT OVERLAPS` for `PRIMARY KEY` and `UNIQUE`, and by `PERIOD` for foreign keys, all applied to the last specified column."
- Gives valid-time integrity natively. System time is not provided by core (the fetch tool said "my understanding", UNVERIFIED; check docs). Cloud SQL version support for PG18 was not checked: Gap.
- Vs ours: use range column `valid_during daterange` with WITHOUT OVERLAPS if Cloud SQL runs PG18; otherwise an exclusion constraint on the same range achieves the same. System time = our own `ingested_at`/`superseded_at` columns.

### 2.3 legislation.gov.uk point-in-time
- Source as in 1.4. "As it stood on a date" views via timeline or point-in-time search; each carries a note that a later version supersedes it (WebSearch summary). Different provisions commence at different times.
- Take: "as of" must be per provision (chunk), not per document, since one Act's sections commence on different dates. This affects chunk identity: chunk = (doc_id, provision path, valid range).

### Effect on derived chunks/index/cache
- No production write-up found that covers bitemporal chunks plus a vector index. Notion's per-span hash (1.3) is the closest. Answer cache key already carries `acl_version` (ADR-022); an as-of query would need `as_of` and corpus version in the key. This is my inference, not published evidence.

---------------------------------------------------------------------
## Topic 3. Deletion everywhere

### 3.1 Spotify Padlock (crypto-shredding)
- Source: https://engineering.atspotify.com/2018/09/scalable-user-privacy (Bram Leenders, 2018-09-18) [OLD]; follow-up https://engineering.atspotify.com/2019/9/techbytes-scalable-user-privacy-crypto-shredding-at-spotify (2019-09-04) [OLD].
- Scale as published: designed for "an initial capacity of one million lookups per second"; SLO p99 under 15 ms (normal under 5 ms); availability SLO 99.95%, "might increase this to 99.99%"; "over a thousand microservices"; datasets are petabytes.
- Architecture: all personal data persisted only encrypted; per-user keychain, deleting it "guarantees the data is inaccessible"; root keys never exposed, per-service derived keys; separate key per data category so one category (e.g. targeted ads) can be revoked alone.
- Why they chose it: they rejected (1) a delete endpoint per service ("very difficult to provide any guarantees that it successfully ran on all systems") and (2) tokenization. Immutable datasets: "scanning through petabytes of data every time we want to delete a few rows ... is too expensive."
- Lessons: Padlock downtime means everything that processes personal data is down, so key service availability is the cost.
- Vs ours: per-tenant (or per-document-class) DEK in Cloud KMS is the same idea. Caveat: embeddings leak content semantics but are not decryptable plaintext; encrypting vectors defeats pgvector search, so crypto-shredding covers GCS objects, Parquet, Kafka payloads, backups, but the live index needs physical delete. Take: use crypto-shredding for the places physical delete is hard (backups, Kafka, Parquet, BigQuery), keep real DELETE for OLTP/pgvector.

### 3.2 LinkedIn (Gobblin purge)
- Source: only a secondary write-up found: https://hasgeek.com/PrivacyMode/bpg/sub/best-practices-guide-user-data-anonymization-and-d-8nHAztPQkhLZhUaEV1TGeM (HasGeek, undated). Claim: deletion requests feed a lookup table that Gobblin uses to purge records in the data lake. No primary LinkedIn engineering post found. Treat as UNVERIFIED.

### 3.3 Uber / Apache Hudi
- Uber's own post https://www.uber.com/us/en/blog/apache-hudi-at-uber/ (2026-01-16) does NOT mention deletes or GDPR (fetch result). Scale quoted there: 19,500 datasets (page also says "over 18,000"), about 350,000 commits per day, roughly 6 trillion rows ingested daily, about 350 logical PB, about 70,000 table service operations daily.
- Hudi project blog https://hudi.apache.org/blog/2021/12/16/lakehouse-concurrency-control-are-we-too-optimistic/ (2021-12-16) [OLD]: Uber-linked claim of deletes at "100s of petabytes" via the same Kafka topic as updates, and a multi-hour GDPR deletion job overlapping a half-hourly ingest job risks commit conflicts; suggested single writer. (WebSearch summary; not read directly.)
- Vs ours: Parquet on GCS without a table format cannot do row deletes; rewrite the affected files (partition by tenant makes tenant-level erasure a prefix delete). Take: partition lake data by tenant_id so tenant erasure is delete-prefix, and serialize erasure jobs with ingest.

### 3.4 Lakehouse physical deletion mechanics (Iceberg)
- Sources (secondary, 2026, some possibly AI-assisted so verify against Iceberg docs): https://datalakehousehub.com/blog/gdpr-hard-deletes-on-iceberg/ and https://www.dremio.com/blog/apache-iceberg-and-the-right-to-be-forgotten/ (undated).
- Reported: merge-on-read delete files are removed only after compaction and snapshot expiry; default `history.expire.max-snapshot-age-ms` is five days; versioned buckets keep non-current versions until a lifecycle rule expires them. Sources disagree on whether expire_snapshots or remove_orphan_files deletes data files.
- Take: erasure deadline = delete + compaction + snapshot expiry + object-version lifecycle. On GCS, set Object Versioning off or a short noncurrent lifecycle on the lake bucket.

### 3.5 BigQuery
- Source: https://docs.cloud.google.com/bigquery/docs/time-travel (Google, last updated 2026-10-27 UTC).
- Quotes: time travel window "covers the past seven days by default", configurable 2 to 7 days; fail-safe: deleted data kept 7 more days, "isn't configurable and can't be extended"; fail-safe not directly queryable. Table snapshots persist data longer. Page does not mention GDPR.
- Take: after DELETE, data remains up to 7 + 7 days (default 14; at minimum 2 + 7 = 9 days). State this window in the erasure policy; do not claim instant physical deletion.

### 3.6 Cloud SQL backups
- Source: https://docs.cloud.google.com/sql/docs/postgres/backup-recovery/backups (Google, last updated 2026-10-26 UTC).
- Quotes: "Cloud SQL retains the backups of deleted instances for four days." Standard on-demand backups kept "indefinitely until manually deleted." Final backup default 30 days (1-365 for standard). Automated backup retention 1 day to 10 years depending on option. The page has no statement about removing individual rows from a backup.
- Take: backup retention is the erasure SLA ceiling; document "erased from backups within N days" (N = automated retention) rather than rewriting backups. Per-tenant DEK crypto-shredding is the only way to make backups unreadable earlier, and that needs column/field-level encryption in OLTP, which costs query capability.

### 3.7 Kafka
- Source: https://kafka.apache.org/42/configuration/topic-configs/ (Apache Kafka 4.2 docs, fetched 2026-11-01; note: Confluent Cloud may differ).
- Quotes: `delete.retention.ms` "the amount of time to retain delete tombstone markers for log compacted topics" (default 86400000 ms); `min.compaction.lag.ms` "The minimum time a message will remain uncompacted in the log"; `max.compaction.lag.ms` "The maximum time a message will remain ineligible for compaction"; `cleanup.policy` "delete" or "compact" or both.
- Take: erasure in Kafka = tombstone + `max.compaction.lag.ms` bound, or avoid by keeping PII out of events (IDs only) and short retention on the delete policy. Spotify's approach (3.1) is encrypt payloads. Confluent Cloud tombstone handling was not checked: Gap.

### 3.8 Segment
- Official engineering post not found. Twilio docs reported (WebSearch summary) to remove user records from archives, warehouses and data lakes and to trigger downstream deletions with "deletion receipts"; third-party commentary says unsupported destinations need manual handling. UNVERIFIED. Take only the pattern: a deletion request produces a per-system receipt.

### Not found
- Published "proof of deletion" designs. Closest are receipts (Segment, unverified) and Spotify's single-key argument. No source covered Langfuse trace erasure or log erasure: Gap (check Langfuse docs separately).

---------------------------------------------------------------------
## Topic 4. Cells and data residency

### 4.1 AWS cell-based architecture guidance
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reducing-scope-of-impact-with-cell-based-architecture/reducing-scope-of-impact-with-cell-based-architecture.html (AWS, 2023-09-20) and https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_use_bulkhead.html (undated).
- Quotes: "If a workload uses 10 cells to service 100 requests, when a failure occurs in one cell, 90% of the overall requests would be unaffected." Cell router: "the thinnest possible layer". Anti-patterns: "Allowing cells to grow without bounds", deploying to all cells at once, "Adding complex business or routing logic to the router layer". Partition key examples: customer ID. "Depending on the workload, a cell migration strategy may be needed ... if a particular user or resource ... becomes too big". Cell max size set by load testing; grow by adding cells. Multi-Region "usually not required for most workloads".
- Vs ours: one stack per region with tenant_id as partition key; router = a tenant-to-region lookup. For 2-3 firms the guidance itself says multi-region is usually not required; a tenant `region` column plus single region now is the compatible step.

### 4.2 Atlassian data residency [OLD]
- Source: https://www.atlassian.com/blog/atlassian-engineering/how-we-build-data-residency-for-atlassian-cloud (Geeves, Moes; 2021-08-26) [OLD].
- Scale as published: six initial regions; page loads about 500 ms faster at p90 after moving EU customers to Ireland; tenants with "5+ million, or even 10+ million" Jira issues; sharding the Issue Service index into 10 shards allowed migration of the largest tenants "in under 60 minutes"; Tenant Context Service serves millions of requests per minute.
- Architecture: central control plane (Cloud Provisioner on AWS SWF, Catalogue Service, Tenant Context Service); each product instance has a realm defining allowed AWS regions; residency covers at-rest primary user content; services are sharded with canonical shard per instance.
- Tenant move: two phases, copy first, delete only after all copies complete; reframed as "addition of data to regions" and "removal of data from regions"; on failure, re-online the tenant first, then delete partial copies.
- Lessons (page): design rollback to be more reliable than the happy path; queued events can wait hours so consumers must verify the tenant's region when reading a message; replicate only where needed; onboard services progressively.
- Later: Atlassian support doc https://support.atlassian.com/security-and-access-policies/docs/move-data-to-another-location/ says a move takes the app offline (WebSearch summary, undated). A third-party blog claiming up to 24 h downtime is not reliable.
- Take: copy-then-delete tenant move; region check at consume time (applies to our outbox/acl-applier).

### 4.3 Slack
- Cells: https://slack.engineering/slacks-migration-to-a-cellular-architecture/ (Cooper Bethea, 2023-08-22). Cells are AZs, not residency units; trigger was the 2021-06-30 AZ network fault; control plane (Rotor) is replicated regionally; "Core computational infrastructure remains in us-east-1"; drain mechanism must not rely on the AZ being drained. Over about 1.5 years migrated the most critical services.
- Residency: https://slack.com/help/articles/360035633934-Data-residency-for-Slack (Slack help, undated): data kept in a single region per customer; existing customers stay in US unless migrated by Slack sales; some categories (member profiles, IDs) may sit outside the chosen region.
- Take: even Slack keeps some identity metadata global; decide explicitly which fields are global (user id, email, tenant membership list) and say so in the privacy notice.

### 4.4 Salesforce Hyperforce
- Sources: https://architect.salesforce.com/docs/architect/fundamentals/guide/platform-transformation.html (undated) and https://engineering.salesforce.com/behind-the-scenes-of-hyperforce-salesforces-infrastructure-for-the-public-cloud-429309542d8e/ (about 2.5 years old per search tool; date not confirmed). Reported: a grid is multiple instances sharing one control plane; control plane hosts services to create, manage and monitor instances; cells and supercells scale horizontally with limited blast radius. Org migration details not retrieved: Gap.

### 4.5 Login for users in several regions
- WorkOS https://workos.com/blog/data-residency-for-enterprise-saas (2026-01-29) says the control plane including authentication may stay global while content stays in region (example: OpenAI ChatGPT Enterprise EU residency, Slack TIA quote "login requests will be sent to the U.S."). It does NOT cover users who belong to orgs in several regions.
- No close published match for multi-region membership login. Pattern implied by 4.1/4.2: global identity record (one login), global tenant directory mapping tenant to region, user picks tenant, router sends to that region's data plane; token carries tenant claim. Identity Platform multi-tenancy is per-tenant user pools, so a person in two tenants has two identities unless we link them: Gap for the design to decide.

### Stripe, Notion cells
- No residency/cell write-up retrieved for Stripe or Notion. Notion's sharding posts (https://www.notion.com/blog/sharding-postgres-at-notion, 2021-10-06 [OLD]; https://www.notion.com/blog/the-great-re-shard, 2023-07-17 [OLD]) are workspace-ID sharding, not residency. Useful migration framework from the 2021 post: double-write, backfill, verification, switch-over; "compare record versions before writing old data, skipping records with more recent updates" so backfill and catch-up can run in any order.

---------------------------------------------------------------------
## Topic 5. Reconciliation and data quality

### 5.1 Dagster asset checks
- Source: https://dagster.io/docs/guides/test/asset-checks (Dagster docs v1.13.28, 2026, undated).
- Facts: `@asset_check`/`@multi_asset_check`; by default downstream still materializes on failure; `blocking=True` stops downstream; results in UI with metadata and severity; partitioned checks show per-partition status; checks can run on their own schedule with a sensor alert; "Each check should test a single asset property."
- Take: use blocking checks at bronze->silver for row-count/hash reconciliation per (tenant, source_version); non-blocking for gold freshness.

### 5.2 Airbnb reconciliation framework [OLD]
- Source: https://medium.com/@winnie.xiong/a-generic-reconciliation-framework-to-do-automatic-health-check-for-airbnb-data-291143b34b6a (Medium, tool reports about 2411 days old, so roughly 2020) [OLD]. Reported: sanity, cross, completeness and regression checks; 11 cross checks between upstream events and downstream accounting data. Partial match (finance, not row counts per stage). Not fetched directly.

### 5.3 Uber Hudi (observability lesson)
- From 3.3: "Continuous automated monitoring and validation catch silent issues, such as corrupted files" and "Failures are inevitable, but recovery must be fast and safe." (https://www.uber.com/us/en/blog/apache-hudi-at-uber/, 2026-01-16)

### Not retrieved
- OpenLineage and dbt tests/source freshness: no production write-up read this round. Gap. Note OpenLineage emission has Dagster integration, but I did not verify it.

---------------------------------------------------------------------
## Topic 6. Re-embedding and blue-green vector index

### 6.1 Notion (production)
- Source: https://www.notion.com/blog/two-years-of-vector-search-at-notion (2026-02-19).
- Scale as published: "multi billion object workload"; migration from pod clusters to serverless May 2024; to turbopuffer evaluation and migration May 2024 to January 2025.
- Architecture: sharded by workspace ID; when indexes filled, new "generation" with its own ID chosen, new workspaces routed there. During migration: "Full re-indexing", "Embeddings model upgrade", and "Gradual cutover: We migrated generations one at a time, validating correctness before moving to the next". Results: 60% reduction in search engine spend, 35% reduction in AWS EMR compute, p50 latency from 70-100 ms to 50-70 ms.
- Lesson: they combined model change with infra change in one reindex, and cut over per tenant-group (generation), not globally.
- Vs ours: per-tenant cutover is natural with LIST partition per tenant: build `chunks_v2` embeddings per tenant, flip a per-tenant `embedding_version`.

### 6.2 Practitioner pattern (not a big-system write-up)
- Source: https://tianpan.co/blog/2026/07/05/retiring-an-embedding-model-reindex-without-downtime (Tian Pan, 2026-07-05). Steps: build new index alongside old; dual writes ("Dual writes freeze the delta at zero"); backfill without overwriting fresher vectors; atomic alias flip, rollback = reverse; golden query set recall@k; shadow traffic over days; keep old index for a rollback window. Handle hard deletes mid-migration or pause them. Worked example: 100 million chunks at about 400 tokens = roughly 40 billion tokens, about $5,200 at about $0.13 per million tokens (about $2,600 batch), more than five days at 5 million tokens per minute. Single-author blog, numbers are the author's example.
- The web search found other guides (mixpeek, zilliz, hackernoon); none is a first-hand production report. The claim that Uber and Pinterest use blue-green for vectors is UNVERIFIED.
- Take: our corpus (2-3 firms) is tiny, so cost is trivial; the real requirement is per-vector `model_id`, erasure applied to both versions during overlap, and a golden-query recall gate.

---------------------------------------------------------------------
Takeaways for our design:
- Store an opaque source change token plus a per-chunk content hash, poll feeds with an overlap, and run periodic full-listing diff to catch hard deletes, because cursor sync misses deletes and silent edits (Airbyte 1.2, Google Drive 1.1, Notion Page State 1.3).
- Model "known amendment, not yet applied" and per-provision valid ranges as explicit states; "as of" granularity is the chunk/provision, with `WITHOUT OVERLAPS` on PG18 if available (legislation.gov.uk 1.4/2.3, PostgreSQL 18 2.2).
- Treat erasure as per-system with documented windows: physical DELETE in OLTP/pgvector, tenant-prefix delete in GCS/lake with versioning off, BigQuery 7+7 days, Cloud SQL backup retention as the SLA ceiling, Kafka tombstone plus `max.compaction.lag.ms` or keep PII out of events; use per-tenant key crypto-shredding only where physical delete is impractical (Spotify 3.1, BigQuery 3.5, Cloud SQL 3.6, Kafka 3.7, Iceberg 3.4).
- Put `region` on the tenant row and a thin tenant-to-region directory now; multi-region is not needed at 2-3 firms. When moving later, copy then delete, re-online first on failure, and check region at consume time (AWS 4.1, Atlassian 4.2). Multi-region-membership login has no published match: decide yourself.
- For model change, version every vector with `model_id`, dual-write plus golden-query recall gate, per-tenant cutover, and apply deletes to both versions during overlap (Notion 6.1, Tian Pan 6.2); use Dagster blocking asset checks for stage reconciliation (5.1).

Gaps:
- No primary LinkedIn, Uber or Segment deletion write-up found (Uber's own Hudi post is silent on deletes); LinkedIn and Segment items are secondary/unverified.
- No source for erasure in Langfuse Cloud traces, Cloud Logging, or Confluent Cloud tombstone behavior; no "proof of deletion" design.
- No Stripe, Notion residency, or Hyperforce org-migration detail; no published multi-region-membership login pattern; Identity Platform behavior for one person in several tenants not checked.
- OpenLineage, dbt tests and Fivetran not covered; Airbnb reconciliation post not read directly and is old.
- No commercial legal-data provider write-up (Westlaw/Lexis); legislation.gov.uk facts came from search summaries, not fetched pages.
- Cloud SQL PG18 availability not checked; SQL:2011 system-versioning absence in core PG is unverified.
- Exa was rate limited; coverage of topic 2 (bitemporal at scale) is thin.
