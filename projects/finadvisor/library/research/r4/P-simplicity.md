OPTIONS

# P-simplicity: round 4 design, lens SIMPLICITY

Written 2026-11-02. Lens: fewest moving parts and tickets that still meet the brief's "done when"; one person can run it.
Tags are those of evidence-r4.md (CONFIRMED, CORRECTED, UNVERIFIED, UNSUPPORTED, [PREPRINT]). "ESTIMATE" = my arithmetic, not a source. "INFERENCE" = my reading of a source, to be tested. Section refs `ev §` = evidence-r4.md.

## 0. Principles that make this small

1. No new running service. Everything new is a table, a column, a job entrypoint, a worker role, a static file or a test. Count: 0 new services, 0 new SaaS, 1 new Postgres table family (`document_versions`, `deletion_requests`, `deletion_ledger`, `source_state`), 3 new worker/job roles (`eraser`, `reconcile`, `source-sync`).
2. Bronze is the source of truth for replay; Kafka is a pipe, not a store. Short Kafka retention then costs nothing for recovery and bounds erasure.
3. Keep data in slow-to-delete stores pseudonymous and redacted (already ADR-014/D13j) instead of adding per-subject KMS keys.
4. Declarative `reconcile_lineage()` instead of ordered event handling: one idempotent code path covers late, out-of-order, withdrawn and replayed versions.
5. Residency by replication of one cell definition, with a static JSON directory instead of a live control plane.
6. Measure before adding a method (D-R4-3): every new RAG or guardrail method is an arm with a pass line; several are built only if a trigger fires.

## 1. Assumptions and numbers (flagged)

| # | Assumption | Basis |
|---|---|---|
| A1 | First-set corpus about 30 MB text, about 7.5M tokens, about 19k child chunks (400 tokens) plus parents; about 150-250 documents (versions counted) | ESTIMATE from ev §1.4: 17 CFR 275 225 KB x about 25 version dates; EU PRIIPs 9 files about 0.5-1 MB; MiFID II EN+DE 2 versions; 3 x 10-15 497K at about 100 KB; 10-20 ADV brochures; few KIDs |
| A2 | Postgres stays 16 + pgvector 0.8.5 (arch §5). PG18 temporal keys are NOT adopted | arch binds PG16 + pgvector 0.8.5 (ADR-008, E0 image `pgvector:0.8.5-pg16`); ev §2.2: no cascade through temporal FK; Cloud SQL PG18 is available (CONFIRMED) so it stays a later option |
| A3 | Demo load unchanged: about 10 QPS peak, 2-3 firms + PUBLIC; budget $100-200 (E10 expects $110-160) | overview §1.2 |
| A4 | Ingest events 1-5k/day (ADR-013); real-source changes are a few per week | ev §1 update frequencies |
| A5 | Personal data in the system is synthetic (D-R4-2). Erasure design is built and tested on synthetic subjects; documents are the real data | brief D-R4-2 |
| A6 | Anthropic Sonnet 5.5 list price is not in evidence; eval-run cost below uses an assumed $3/$15 per MTok (UNVERIFIED) | pricing page to be read in the first E7 ticket |

Back-of-envelope (ESTIMATE):
- Embed whole corpus: 7.5M tokens x $0.06/M (voyage-4) = $0.45; first 200M tokens free (ev §2.5) so $0 in practice. Re-embed at voyage-4-large $0.12/M = $0.90. At 1M chunks (400M tokens): $24 (voyage-4) or $48 (large); at 8M TPM = 50 min (voyage-4 tier 1; ev §2.5).
- pgvector size: 19k x 1024 halfvec (2 KB) = 38 MB per embedding column; two columns during blue/green = 76 MB plus HNSW (about the same again). Fits the 8 GiB instance with room.
- Model Armor ingest screening: about 6M billed tokens per full pass (4 chars excluding whitespace) minus 2M free = about $0.40 per full pass (ev §4.4); per-chunk windows of about 1k tokens = about 7-8k calls; throttled to 300 QPM = about 25 min.
- Golden-set eval run: 200 items x (about 8k in + 1k out) = 1.6M in + 0.2M out; at the assumed price about $8 per full run; 10 arm-runs per ablation round = about $80 once, not monthly.
- Re-reconciliation: set hashes over about 19k rows = seconds; Cloud Run job cost about $0.

## 2. Diagram (changed parts only)

```
 SOURCES (6 connectors, 3 code shapes)             CONTROL (static, no service)
 eCFR | CELLAR | legislation.gov.uk | EDGAR        directory/<slug>.json in control bucket
 FCA API | manifest (KID, ADV, ESMA, 497K URLs)    {display_name, idp_tenant_id, cell, api_base}
        |  source-sync job (Dagster asset, per source)               |
        v  watermark poll + weekly full-listing diff                 | SPA reads, calls api_base
  source_state (watermark, last_listing_hash)                        v
        v                                   ============ CELL (us | eu), identical definition ============
  bronze GCS  sha256 + document_versions row (status: pending_scan)    Kong -> chat-api -> Cloud SQL
        v  ingest scan: strip hidden text + Model Armor per chunk      worker pool, Kafka (cell cluster)
  quarantine? --yes--> document_versions.status=quarantined, not indexed   GCS bucket, BigQuery dataset
        v no                                                              Langfuse project, Model Armor endpoint
  silver (Docling, Presidio, structure chunking, Pandera), 1 Parquet per document version
        v
  reconcile_lineage(doc): derive target chunk set from ordered versions,
                          diff on (section_path, chunk_hash, valid_from), embed new hashes only,
                          one tx, bump corpus_version
        v
  chunks(valid_from, valid_to, emb_a, emb_b)   <-- retrieval WHERE valid at :as_of (DB date)
        v
  reconcile job (nightly while up, weekly always): counts + set-hashes source->bronze->silver->chunks->BQ

 DELETION: deletion_requests (Postgres table = the queue, no Kafka) -> eraser role ->
   Postgres tx | GCS objects | BQ DML | Langfuse batch delete | cache purge -> deletion_ledger receipts
   Kafka and backups: expire by retention (documented windows), restore re-applies the ledger.
```

## 3. Decisions

Format per decision: Choice; Rejected; Evidence; Cost delta/month; Strongest dissent.

### 3.1 Real data onboarding (Track 1)

**D1. First source set and connectors.**
- Choice. One `Connector` protocol with three methods: `list_changes(watermark)`, `full_listing()` (identity + version tag only), `fetch(item)` returning bytes plus metadata (licence, attribution, lang, valid_from, source version key). Six implementations:
  1. eCFR (17 CFR 275 whole part; 270 optional): `versions/title-17.json?part=275` diff, point-in-time `/full/{date}/`; gzip header, 1 rps.
  2. CELLAR: SPARQL for PRIIPs 1286/2014 (3 versions x EN/DE/FR), RTS 2017/653, MiFID II EN+DE 2 versions, 1 corrigendum; poll `cdm:lastModificationDate`; XHTML only (HTML/PDF 404).
  3. legislation.gov.uk: eur/2014/1286 "(revoked)" + 3 of 12 point-in-time versions, 2017/565, 2017/653; `/update` Publication Log feed; 1,500 req / 5 min cap (use 1,000); mandatory User-Agent.
  4. EDGAR: per-CIK submissions JSON + weekly full-index reconcile for 3 fund families; 497K only (no 485BPOS); 10 rps cap, use 2; declared User-Agent.
  5. FCA Handbook API: COBS 9A and 6, current text only, free account; hash-compare each run; revocation switch (D9).
  6. Manifest connector: a YAML list of URLs (KIDs iShares EN+DE, DWS DE; 10-20 ADV brochures; ESMA Q&A snapshots 2022-12-21 and 2025-12-05; ESMA Prospectus Q&A "Deleted" overview). HEAD + weekly re-fetch and hash compare. Keshav writes the URL list once.
- Not in the first set: FINRA (terms, ev §0.2), EDGAR full-text search (403), companyfacts (404 for funds), RR datasets (optional cross-check, dropped for simplicity; add only if the tables ablation shows XBRL lookup wins), Data Dump, FCA Register API, FCA non-Handbook pages, IAPD scraping (URL pattern undocumented: manifest instead).
- Rejected: per-source bespoke pipelines (3x tickets); Debezium/CDC (sources are HTTP; no DB); crawling FCA (cl.35.3 ban, CONTRADICTED crawl plan).
- Evidence. ev §1.1-1.4 (access, limits, verdicts); K-R4-2, K-R4-3.
- Cost. About +$1 (Model Armor, Voyage, GCS). Egress to public APIs: negligible.
- Dissent. Reliability: six connectors with six failure modes is too many for week one; start with eCFR + CELLAR + EDGAR. Reply: the brief's done-when needs 3 jurisdictions, deletes, >1 language and tables; the minimum covering set is exactly eCFR (US versions + removals), CELLAR (EU, 3 languages), legislation.gov.uk (UK revoked), plus manifest (tables, withdrawals). FCA and EDGAR-per-CIK are the two droppable connectors if time runs out; ticket order puts them last.

**D2. Mapping of synthetic firms to real documents.**
- Choice. Regulation and licensed text go to the PUBLIC tenant (written only by `etl-public`, in-process, never on Kafka); fund/adviser documents with no licence go into the firm tenant that uses them (its product shelf), never into PUBLIC. New columns on `documents`: `lang`, `licence`, `attribution`, `authentic bool`, `source` (extend enum).

| Source | Tenant | jurisdiction tag | tier_required | licence / disclosure carried |
|---|---|---|---|---|
| eCFR 17 CFR 275 | PUBLIC | US | 1 | US gov |
| CELLAR PRIIPs/MiFID II/RTS EN,DE,FR | PUBLIC | EU | 1 | CC BY 4.0 + "not authentic" flag (`authentic=false`) |
| legislation.gov.uk | PUBLIC | UK | 1 | OGL v3.0 + attribution |
| FCA COBS (API) | PUBLIC (own `source='fca_api'`) | UK | 1 | OGL + (c) FCA; revocable |
| ESMA Q&A snapshots | PUBLIC | EU | 1 | ESMA transformed-text disclaimer (D12 compliance checks) |
| 497K (3 fund families) + ADV brochures (10-20) | firm F-US shelf | US | 2 | `licence='unknown'`, private-only |
| KIDs iShares EN+DE, DWS DE | firm F-EU shelf; the same files also in F-UK shelf | EU (regime date tagged) | 2 | `licence='unknown'`, private-only |
| Synthetic internal policies | each firm (unchanged) | per firm | 3-4 | synthetic |

- The same KID in F-EU and F-UK is deliberate (edge case "duplicate document in two firms").
- Publisher documents are fetched by the `etl` job at demo time into the private bucket; the repo and public eval sets contain no text from them (K-R4-3).
- Rejected: all real docs in PUBLIC (exposes unlicensed documents to every tenant, wrong for the product even if the demo is private); a fourth "restricted" tenant kind (new RLS branch, new tests).
- Evidence. ev §1.4 notes; K-R4-3; ADR-002/D13a write split.
- Cost. $0. Dissent. Learning value: a restricted tenant kind would exercise RLS more. Reply: not needed to meet any done-when.

### 3.2 Change capture (Track 2)

**D3. Capture algorithm, same for every connector.**
- Choice. `source_state(source, watermark, last_full_listing_hash, last_full_listing_at)`.
  - Fast path every 6 h while the demo is up, daily otherwise via Scheduler: `list_changes(watermark - overlap)`, overlap = 3 days. Dedupe by `(source, item_id, version_key, sha256)`.
  - Backstop weekly: `full_listing()` diffed with `document_versions`. Items missing from two consecutive listings become `withdrawn`. Items present with a new hash become a new version.
  - Mass-withdrawal breaker: a run that would withdraw more than 5 documents or 10% of a source is held for manual approval (a partial or empty listing from an outage must never delete data).
  - Order independence: arrival order is irrelevant because `reconcile_lineage()` (D5) sorts versions by `valid_from`.
  - Per source: eCFR `removed:true` = repeal (valid_to), `substantive:false` = editorial (new version, same text hash skips embedding); CELLAR `date_end-of-validity`/repeal = valid_to; legislation.gov.uk "(revoked)" title = valid_to, "applied/unapplied" effects lag 4-8 weeks (secondary) = disclosure text "source may lag"; EDGAR corrections only show in the weekly Saturday full-index (so the weekly diff is mandatory there); ESMA "Deleted" overview and manifest hash change = withdrawal; FCA API absent item = withdrawal; FCA revocation = D9.
- Rejected: webhooks/RSS-driven only (CELLAR RSS registration UNVERIFIED, EDGAR has none); a Dagster sensor daemon (arch: daemon-less); per-source CDC tables.
- Evidence. ev §2.1 (Airbyte cursor misses hard deletes: full-listing backstop; Drive Changes token), §1.1-1.3 per source change signals.
- Cost. $0 (HTTP + Cloud Run job seconds). Dissent. A two-strike withdrawal rule delays a real withdrawal by up to a week; reply: a source withdrawal is not an emergency except FCA revocation, which has its own switch (D9).

### 3.3 Versioning (Track 3)

**D4. Valid time on chunks, system time on version rows, no PG18 temporal.**
- Choice.
  - New table `document_versions(tenant_id, document_id, version_key, valid_from date, source_published_at, bronze_sha256, bronze_uri, fetched_at, ingested_at timestamptz, withdrawn_at timestamptz NULL, status in (pending_scan, active, quarantined, withdrawn), parser_version, pipeline_run_id)`. `documents` becomes the lineage row (one per law / fund series); `bronze_*` columns move to versions. `documents.in_force_until date NULL` records repeal.
  - `chunks` gains `valid_from date NOT NULL`, `valid_to date NULL` (exclusive), `version_key`. Validity is per provision (chunk identity = lineage + section_path + chunk_hash + valid_from), matching legislation.gov.uk where commencement differs per section (ev §2.2). Unique key becomes `(tenant_id, chunk_hash, embed_model, valid_from)`; unchanged sections across versions keep one open-ended row.
  - Valid time is a calendar date, `valid_from` inclusive, `valid_to` exclusive, UTC date. Overlap guard: partial unique index on `(tenant_id, document_id, section_path, chunk_index) WHERE valid_to IS NULL`, plus a SQL invariant test (no two rows for one provision overlap) run in L0 and by the reconcile job. An `EXCLUDE USING gist` constraint with `btree_gist` is the upgrade if the invariant ever fails (extension listed for Cloud SQL, PG16 availability UNVERIFIED).
  - System time = `ingested_at` / `withdrawn_at` on versions plus immutable bronze: "what did we hold on T" is answerable per version, not per chunk. Chunk-level system-time history is not kept (physical replace on re-parse).
  - "As of" query: retrieval SQL adds `valid_from <= :as_of AND (valid_to IS NULL OR valid_to > :as_of)`. `:as_of` is the user date if the request states one (validated 2000-01-01..today) else `current_date` read from the database once per request (never the instance clock). Default policy: today. The SPA offers an optional date field; the agent tool schema gets `as_of` (a date, not a tenant/tier/jurisdiction, so ADR-004 holds).
  - Answer cache key adds the resolved `as_of` date. Cache already carries `corpus_version`; a PUBLIC change bumps it, and hits re-verify against fresh chunks, so a retired chunk is a miss (ADR-015 unchanged otherwise).
  - Index: no extra index; the filter applies after the ANN scan like tier/jurisdiction, so iterative scan (already mandatory) covers it. The L1 test checks no short results with an old `as_of` (many rows filtered).
  - Staleness (existing, from `last_reviewed_at`) is computed against the as-of date for past queries; output states "answer reflects text in force on <date>".
- Rejected: PG18 `WITHOUT OVERLAPS` + PERIOD FK (departs from the binding PG16 arch and the E0 CI image, and cannot cascade, ev §2.2); XTDB or full bitemporal tables (conflicts with erasure, not adoptable at demo budget, ev §2.2); one document row per version with validity on the document (re-embeds unchanged provisions; breaks per-provision commencement); chunk-level `retired_at` history.
- Evidence. ev §2.2 (PG18 limits; per-provision point-in-time; no production write-up of bitemporal chunks; cache key inference); FiscalQA Pro [PREPRINT] direction only (E2: hard filter beats current-only; magnitude not transferable).
- Cost. About +20 MB Postgres; $0.
- Dissent. Reliability: no chunk-level system time means "what exactly did the retriever see on 5 March" is replayable only by re-running with that corpus snapshot. Reply: messages already persist cited chunk text and `corpus_version`; legal audit needs the answer and its sources, which are stored. Keep as a trigger: if auditors need retrieval replay, add `retired_at` and stop physically deleting superseded chunks (erasure then needs a second path).

**D5. One idempotent `reconcile_lineage(document_id)`.**
- Choice. Inputs: all non-withdrawn, non-quarantined `document_versions` of a lineage in `valid_from` order and their silver Parquet. Output: target chunk set keyed by `(section_path, chunk_index, chunk_hash, valid_from)` with `valid_to` = start of the next version that changes that provision, or NULL. Apply as a diff in one transaction under `pg_advisory_xact_lock(lineage)`: insert missing rows (embed only new `chunk_hash` values, reusing vectors of rows being replaced), update validity metadata in place (no re-embed, like ADR-022), delete extras, bump `corpus_version`. Late/out-of-order version, withdrawn version, parser bump, replay after a bug fix and backfill are all "run it again".
- Tenant path (worker `indexer`) and PUBLIC path (`etl-public`) call the same function; this also removes the "two paths must stay identical" risk named in ADR-014.
- Rejected: event-ordered incremental updates (need ordering guarantees across Kafka partitions and sources); full re-ingest on every change (re-embeds; ev §2.1 Notion per-span hash is the precedent for hash skip).
- Evidence. Notion span hashing (ev §2.1, CONFIRMED 70% data reduction, not the 60%/35% figures); ADR-022 metadata-only UPDATE.
- Cost. $0. Dissent. A lineage-level lock serialises ingest per document; fine at 150 lineages.

### 3.4 Deletion everywhere (Track 4)

**D6. Physical delete everywhere it works; windows capped by configuration; no per-subject KMS keys.**
- Mechanism. `deletion_requests(tenant_id, id, scope in (document, source, advisor, tenant), subject_id, reason in (erasure, takedown, source_withdrawal, offboarding), requested_at, status)` is a Postgres table that is also the queue: the `eraser` role (in `fa-worker`, `fa_worker` grants plus DELETE on the extra tables) polls it with `FOR UPDATE SKIP LOCKED`. Kafka is not on the delete path, so a Kafka outage cannot delay deletes. ADR-022's `acl-applier` moves to the same polling (Kafka event kept for analytics only): a simplification, not an addition.
- Per-store steps (idempotent; each writes a receipt into `deletion_ledger.receipts` with count and post-check):

| Store | Mechanism | Window after eraser step | Config lever | Evidence |
|---|---|---|---|---|
| Postgres live | one tx: `answer_cache` rows by `source_document_ids`, `chunks`, `suitability_rules`, `ingest_rejects`, `document_versions`, `documents` (children first; no cascade through temporal FKs and none is used); for an advisor: `messages`, `turn_events`, `feedback`, `escalations`, `conversations`, then the `advisors` row; bump `corpus_version` and `acl_version` | immediate | none | ev §2.3 |
| Postgres backups | no per-row purge exists; retention 7 days (automated backups, demo profile), PITR off in demo; on restore the `replay-ledger` job re-applies every ledger entry before traffic | up to 7 d; PITR log retention NOT FOUND, so prod profile claims nothing until measured | `backupRetentionSettings` 7 | ev §2.3 (1 d-10 y configurable, no row purge); restore replay is INFERENCE |
| GCS bronze/silver | delete objects by generation; silver is one Parquet per document version so one object is deleted; data bucket soft delete set to 0 (re-fetchable data) | immediate | `softDeletePolicy 0` | ev §2.3 (soft delete 7 d default, 0 disables) |
| BigQuery | `DELETE ... WHERE doc_id/advisor_ref IN (...)`, batched into one statement per eraser run, run at least 30 min after the request (streaming buffer), one statement at a time per table | 2 d time travel + 7 d fail-safe = 9 d after the DELETE, at most 10 d after the request | dataset `max_time_travel_hours = 48` | ev §2.3 (2-7 d time travel, fail-safe 7 d not configurable; DML limits 2 concurrent + 20 queued) |
| Kafka (Confluent Basic) | payloads minimised; no compacted/tombstone topics for subject-linked data; all event topics `retention.ms` 7 d, `segment.ms` 1 d; PUBLIC and FCA content never enters Kafka (in-process path) | at most about 8 d (INFERENCE: closed segments expire) | topic configs | ev §2.3 (compaction min 7 d, retention max on Basic NOT FOUND: verify in E5) |
| Langfuse | for advisor erasure only: list traces by `userId`/`sessionId`, batch `DELETE`, re-query to verify; document deletion needs no Langfuse step (spans carry chunk ids, `capture_output` off on retrieval) | about 15 min typical, not guaranteed | none | ev §2.3 (no confirmation returned; dataset items after trace delete NOT stated) |
| Cloud Logging | PII-free by design (Kong whitelist, no bodies); no per-entry delete; `_Default` retention 30 d | 30 d for non-personal operational logs | bucket retention | ev §2.3 (CORRECTED: only whole-log delete) |
| Valkey | counters only, keyed by hash | n/a | none | arch §4.6 |

- Tombstone = row, not message. `deletion_ledger(tenant_id, id, scope, subject_hash, source_uri_hash, bronze_sha256 list, requested_at, completed_at, receipts jsonb)` holds hashes only, no content, and is exported to BigQuery `deletion_ledger` (so it survives a Postgres restore). Every writer consults it: connectors skip blocked `(source_uri_hash, sha256)`; `reconcile_lineage` skips withdrawn versions; the indexer takes `FOR SHARE` on the document row and drops late chunks of a document that is `deleting`/`deleted` (race "delete during ingest"). The nightly reconcile job also runs a resurrection check: any chunk/object whose document is in the ledger raises an alert and is deleted.
- Proof of deletion = receipts + weekly `erasure-audit` job: for each ledger row older than a store's window, re-query Postgres (count 0), GCS (list prefix empty), BigQuery (count 0), Langfuse (re-query), and assert Kafka topic configs unchanged. Output is a table `deletion_ledger.verified_at` per store. This is a self-attested control, not third-party proof.
- Crypto-shredding: not used. Reasons: embeddings in the live index cannot be encrypted without losing ANN search (ev §2.3 BC inference); key destruction effect on standard Cloud SQL backups, replicas, PITR and on GCS is undocumented (ev §2.3), so it would give an assurance nobody can verify; BigQuery AEAD shredding is "design inference, no doc describes it"; KMS write quota 100 TPM adds bursts. Instead pseudonymisation: Kafka/BigQuery/Langfuse carry `advisor_id` (random uuid) and redacted text only; erasing the `advisors` row (name, `idp_uid`) in Postgres and the IdP user unlinks the remaining copies in the slow stores. Spotify's Padlock guarantee also covers only the keychain, not derived copies (ev §2.3).
- Rejected: per-subject KMS keys ($0.72/yr each, ev §2.3, cost is not the issue; verifiability is); Kafka compaction + tombstones (7 d minimum compaction lag, ev §2.3, worse than retention expiry); Iceberg/Hudi (secondary claims only, UNSUPPORTED).
- Cost. Backups 7 d, +$1-3; BQ DML free in the 1 TiB query budget at this size; eraser $0.
- Dissent. Reliability/compliance: self-attested proof and a documented-only window are weak; per-subject keys would let you say "unrestorable". Reply: the key route is unverifiable on the stores that matter, and subjects here are synthetic; revisit when real personal data arrives (ADR-013/018 trigger already says so).

**D7. Erasure SLA wording (honest).**
"Requests are accepted immediately. The subject's data is removed from search, answers, caches and the live database within 15 minutes (target; Postgres and cache are immediate, trace deletion is 'usually within 15 minutes'). Copies in the analytics warehouse are deleted within 1 day and then pass through the warehouse's own 9-day recovery window; message-bus copies expire within about 8 days; database backups roll off within 7 days, and a restore re-applies the deletion before use. Operational logs hold no personal data and expire after 30 days. All personal data is therefore gone from every store no later than 10 days after the request; documented windows, not yet measured end to end; checked weekly by an erasure audit. Deletion is not instant in backups or analytics." Where 10 d = 1 d (BQ step delay) + 9 d (BQ windows); Kafka 8 d and backups 7 d are below that. The 10-day figure is ESTIMATE from documented windows (ev §2.3), to be replaced by a measured number from a drill (E-deletion ticket). Do not publish "30 days" or "instant". Not legal advice; Keshav decides final wording (open item in ev §0).
- Dissent. "10 days" invites a challenge when BigQuery fail-safe is documented as non-configurable; keep the arithmetic visible.

**D8. Source takedown and FCA revocation.**
- Choice. Same `deletion_requests` with `scope=source`, plus a one-command runbook `revoke-source fca_api`: all FCA rows deleted from Postgres and GCS immediately (soft delete 0), BigQuery holds ids only, Kafka holds nothing because the FCA path is the in-process PUBLIC path. This satisfies cl.13 "immediately delete all copies" (ev §1.3) for all stores, at no extra mechanism. Connector auto-suspends on 401/403. Publisher takedown uses the same path; their text may sit in Kafka up to 8 d (tenant path), disclosed in the runbook.
- Rejected: crawling FCA for history; ignoring revocation risk (OGL vs cl.13 conflict is unresolved, ev §1.3).
- Cost $0. Dissent. FCA API is current-only, rate-limited with no number, format unseen (ev §1.3 gaps): the connector may not be worth it; ticket 1 is a spike with an explicit "drop FCA from first set" exit.

### 3.5 Regional cells (Track 5; K-R4-1)

**D9. Cell = one parameterised copy of the whole data plane; control plane = a static directory.**
- Per cell: Cloud SQL, GCS data bucket, BigQuery dataset (explicit region, not EU multi-region, which excludes London, ev §3.1), Confluent Basic cluster (us-central1 and europe-west2 support Basic, ev §3.1; no cluster links used), Langfuse project (EU Ireland vs US Oregon are separate accounts, ev §3.1), Model Armor regional endpoint, Kong + chat-api + worker + jobs, Valkey. Config key `CELL_ID`; all resource names carry it; a Terraform `cell` module is instantiated once (us-central1). A second instantiation is a variables file, documented and costed, not applied.
- Global: Identity Platform project (treat identity as global, location UNVERIFIED, ev §3.2), the SPA bucket, the directory objects `directory/<slug>.json` = `{display_name, idp_tenant_id, cell, api_base}` written by `migrate --onboard-tenant` (no listing endpoint, so no enumeration beyond today's slug guessing), DNS names `us.api.<domain>`, `eu.api.<domain>`.
- Routing is client-side: SPA loads `/t/<slug>`, fetches the directory object, calls that cell's `api_base`. No global router in the data path. A wrong cell is safe: the token verifies (global IdP) but `fa_tenant_lookup(idp_tenant_id)` finds no tenant there, giving 403 `WRONG_CELL`; nothing is read.
- What never leaves a cell: Postgres, GCS bronze/silver, BigQuery, Kafka, Langfuse traces, answer cache, Valkey. What crosses by design and is stated in the privacy notice: directory fields, IdP identities (email, uid), and model calls (Anthropic first-party has only `global|us`, Voyage regions UNVERIFIED, ev §0.4): redacted text of EU documents and questions is sent to US/global providers. Residency therefore means data at rest (K-R4-1), not inference. Claude on Vertex EU stays a costed option in the ADR.
- Multiple logins. A person in several firms has one Identity Platform identity per firm tenant (tenants are user silos, ev §3.2) and one `advisors` row per tenant, with independent tier/jurisdictions/licences. The SPA keeps one Firebase auth instance per tenant (ev §3.2: `tenantId` is not persisted and `currentUser` does not switch) and a firm switcher; each API call carries the token of the firm in view, and the cell of that firm's directory entry. No global user table, no account linking (tenant limits forbid disabling linking, so linking behaviour is a test). Open test: same email in two tenants (UNVERIFIED, 5-minute live test, ticket 1).
- Moves. (a) Document reclassification: ADR-022 as is. (b) Advisor changes jurisdiction: `UPDATE advisors` + `entitlement_version`, 60 s bound, cache key already carries it. (c) Advisor changes firm: new tenant identity and `advisors` row; old firm data stays with the old firm (it belongs to the firm). (d) Firm changes cell: offline runbook job `tenant-move`: set tenant `moving` (503), copy small OLTP tables for the tenant plus bronze objects to the target cell, re-derive chunks with `reconcile_lineage` (vectors recomputed, about $0.01-0.10 per firm), run reconcile counts+hashes on target, flip the directory object, then run the normal `scope=tenant` deletion in the source. Copy first, delete only after verified (Atlassian pattern, ev §3.4 [OLD]). Analytics history is not moved (BigQuery cannot join across locations, ev §3.1); it is deleted at the source and restarts at the target, stated in the runbook. Downtime = minutes at demo size (not measured).
- Local two-cell test: `docker compose --profile cell-us --profile cell-eu` with `cells/us.env` and `cells/eu.env`; two Postgres, two Kafka, two fake-GCS, one stub IdP issuing tokens for tenants of both cells, one static directory. BigQuery and Langfuse have no local twin in stack.md: the BQ sink target is a config value and residency tests assert dataset location and sink config per cell (a real BQ residency check runs once in the cloud demo). Assertions: tenant X exists only in its cell's Postgres, bucket, topic set, sink target; no cross-cell network path (separate compose networks); wrong-cell call 403; cell-eu down leaves cell-us serving; `tenant-move` end to end.
- Rejected: global external ALB with multi-region NEGs (proximity routing, no tenant pinning, up to 30 min LB convergence, ev §3.1); one global database with a `region` column (residency by policy only); Cloud SQL cross-region replicas (replicate data across regions, the opposite of residency, and Enterprise Plus for DR); a control-plane service with a tenant router (a new always-on component; AWS "thinnest router" is satisfied by no router, ev §3.4); real second region (not built).
- Evidence. ev §3.1-3.4; K-R4-1; AWS cell guidance (blast-radius analogy, not residency; "start with a cell migration mechanism from day one" = `tenant-move`, ev §3.4).
- Cost. Built: $0 (local). Real second cell, option only: unpriced, UNVERIFIED (ev §3.3 "cannot be stated"); main driver Cloud SQL always-on storage + instance; Confluent Basic idles at $0 base; Langfuse second account plan price unread. Estimate it in the ADR from the GCP calculator before anyone approves it.
- Dissent. Reliability: client-side routing means a stale or wrong directory file mis-sends users, and no automatic failover exists. Reply: wrong-cell is a safe 403, failover across regions is explicitly out of scope (residency forbids it for the tenant's data), and the directory is regenerated by the same onboarding command.

### 3.6 Contracts, quality, lineage, reconciliation (Track 6)

**D10. Contracts in code, quality at two gates, lineage by column, reconcile by hash.**
- Contracts. (1) Connector output = Pydantic model `SourceItem` (JSON Schema checked in); (2) Kafka envelopes already Pydantic to JSON Schema registered (ADR-013), compatibility mode set to BACKWARD and tested in CI (default behaviour not read in r4 evidence: UNVERIFIED, verify in E5); (3) silver Parquet validated by Pandera on every document (polars floor `>=1.20.0`, CORRECTED; call `collect()` or set `PANDERA_VALIDATION_DEPTH=SCHEMA_AND_DATA`, else only schema is checked, ev §2.2); (4) dbt gold/BQ marts with `contract: enforced: true` for table models (views check names/types only; ev §2.2). Additive-only schema evolution rule; `schema_version` in every envelope.
- Quality gates. Gate A (silver): Pandera rejects to `ingest_rejects`, non-empty text, language matches manifest, section count within 50-200% of previous version (catches silent parser breakage). Gate B (pre-index): quarantine scan (D13). Blocking asset checks in Dagster are used only within a run (cross-run behaviour UNVERIFIED, ev §2.2), so PII/quarantine gating is also enforced by `document_versions.status` that the indexer checks.
- Lineage. `pipeline_run_id`, `parser_version`, `source version_key`, `bronze_sha256` stored on every `document_versions` and `chunks` row; Dagster's own asset graph is the lineage UI. OpenLineage is dropped: `dagster-openlineage` 0.2.1 had no release in five months, 0.x with removals (ev §2.2). A trace from any answer citation to its source URL is one SQL join.
- Reconciliation (job `reconcile`, Cloud Run, nightly while the demo is up and weekly via Scheduler): per source and tenant, compute counts and `sha256(sorted "id:hash" lines)` at five points and compare adjacent pairs:
  1. source listing vs `document_versions` (count, set hash of `item_id:version_key`);
  2. versions vs bronze objects (list GCS prefix);
  3. versions vs silver Parquet files (one per version);
  4. silver chunk hashes vs `chunks` rows (set hash of `section_path:chunk_hash:valid_from`, expected-vs-actual count; `embedding IS NULL` count 0 for active model);
  5. `ingest_events` per source/day in BigQuery vs published outbox rows.
  Mismatch sets `reconcile_mismatch_total{pair}` (log-based metric), fails the Dagster asset check, and sends the existing alert path (E9). Known benign differences (withdrawn, quarantined) are excluded by status, not by tolerance.
- Backfill and replay. Dagster partitions by `source x month`; replay = re-publish from bronze (arch §7.3) or call `reconcile_lineage` (D5); live traffic is safe because each lineage swap is one transaction and reads see old or new; Voyage rate limit is the throttle. Both honour the deletion ledger (D6).
- Rejected: OpenLineage gate; Great Expectations (second DQ tool, not covered in evidence); row-level CDC between stages.
- Evidence. ev §2.2 (Pandera, dbt contracts, Dagster, dagster-openlineage CORRECTED), §2.1 (Airbnb reconciliation [OLD], partial match).
- Cost. About $0. Dissent. Learning: lineage tooling is a stated learning goal; reply: Dagster's graph already shows lineage and the OpenLineage package is stale; add as an optional epic later.

### 3.7 Re-embedding blue/green (Track 7)

**D11. Two embedding columns in the same row; per-tenant flip.**
- Choice. `chunks.emb_a halfvec(1024)`, `emb_a_model`, `emb_b halfvec(n)` NULL, `emb_b_model` NULL, `tenants.embed_gen char(1) in (a,b)`. Procedure: (1) add `emb_b`, build its HNSW per partition `CONCURRENTLY` (partial `kind='child'`); (2) indexer dual-writes both columns for new chunks; (3) backfill job embeds existing chunks into `emb_b` in batches, no overwrite of rows already filled; (4) gate: retrieval-only recall@10 and nDCG on the golden set (public subset in CI, full set on demo) must not drop more than 2 points paired vs `a` (non-inferiority), and latency p95 within 10%; (5) flip `tenants.embed_gen` per tenant (query embedding model and column move together by config keyed on `embed_gen`, PUBLIC flips last because every tenant reads it); (6) after one week without regression drop `emb_a`. Erasure and `reconcile_lineage` operate on rows, so both versions die together (no second table to forget; ev §2.4 design input "apply erasure to both versions during overlap").
- Scale. 19k chunks: minutes, $0 (free tokens). 1M chunks: 400M tokens, $24-48, about 50 min at 8M TPM (ESTIMATE; real throughput unmeasured, ev §6 gap). Voyage batch: 33% discount but no free credits, so synchronous is cheaper while free tokens last.
- Rejected: second table or index with alias flip (two places to delete from, two schemas); in-place overwrite (no rollback); Notion-style generations by index fill (needed at 100M+ pages, not here).
- Evidence. ev §2.4 (Notion dual-write/backfill/verify/switch; practitioner pattern [single blog]); per-vector model_id.
- Cost. Transient +80 MB; $0-1 per re-embed at demo size. Dissent. Dimension change requires altering a column type later; reply: `emb_b` has its own dimension, which is exactly why it is a second column.

### 3.8 Guardrails on real data (Track 8)

**D12. Ingest scan + quarantine; JSON-encode kept; datamarking is an arm; numeric gate and compliance checks are deterministic code.**
- Ingest scan. Pipeline order: parse, strip hidden text (zero-width and bidi control characters, HTML comments, CSS-hidden elements, `display:none`), Presidio, then screen each parent chunk (about 1k tokens) with Model Armor screening (document screening API for files, text API per chunk) at at most 300 QPM (chat keeps 900 of the 1,200 QPM per-project quota, ev §4.2) and a deterministic pattern list (instruction-like phrases addressed to an assistant). `EXECUTION_SKIPPED` (over 65,536 tokens, 4 MB, modality mismatch) is fail-closed: status stays `pending_scan`, not indexed, retried then alerted. A flagged chunk sets that chunk `quarantined`, excluded from the index; the document goes `quarantined` if more than 3 chunks are flagged. Quarantined items are listed in a table for manual review (the first-set corpus is about 200 documents, so human review is feasible; this is also how false positives on regulatory text, "must", "ignore", "instruction", are measured, ev §4.2 InjecGuard [PREPRINT] over-defense risk). Fallback detectors (Prompt Guard 2 with its gated Llama 4 licence, InjecGuard-class) are not built unless Model Armor misses the pass line below.
- Query time. Retrieved text only inside JSON-encoded `tool_result` (ADR-009, kept). Spotlighting evidence is weak for our case: single preprint, GPT-family, simple keyword payloads, delimiting alone about halves ASR (authors do not recommend it), datamarking broken by payloads without spaces and untested on Claude (ev §4.2). So datamarking is ablation arm A7, not default. If adopted, the marker is applied only to the prompt copy; the numeric gate and quote-overlap verifier run against the stored chunk text with markers stripped, so DE/FR formats like `1.234,56` are not broken.
- Numeric grounding gate. Runs inside the existing sentence buffer: extract numbers, percentages, currency, basis points and dates from each sentence; normalise decimal/thousands separators for EN/DE/FR and `%`/`bps`/unit words; each must appear in the text of that sentence's cited chunks; ranges and rounding allowed by an explicit tolerance table (default exact; rounding to the displayed precision allowed); no derived numbers allowed (a derived figure fails by design and the prompt tells the model to quote, not compute). On failure the sentence is replaced with "[figure not verified in cited source]", `meta.grounding_failed` is set, counter `numeric_gate_reject_total{reason}` increments. No paper tests a plain regex gate (ev §5 E5: FinGround is a different, trained detector, [PREPRINT]); the pass lines below are therefore measured here, not borrowed.
- Deterministic compliance checks (`policy.py`, pure functions of principal and cited-chunk metadata): licence scope (a chunk with `licence='unknown'` can only be cited to advisors of its own tenant: structural by D2, asserted by test); jurisdiction of every cited source within the advisor's set (already RLS, re-asserted on the output); stale-source warning (existing); superseded/revoked warning when `as_of` is past or `in_force_until` is set; "consolidated text, not authentic" notice when `authentic=false`; ESMA disclaimer when an ESMA source is cited (not in any current design, ev §1.4 hidden assumption 4); no suitability statement without the `lookup_suitability_rule` result (existing). Output carries `disclosures[]`; the SPA renders them.
- Per-role tool/output policy. A table `ROLE_POLICY[role] = {tools, output_fields}` in code: `advisor`: three read tools + `escalate_to_compliance`; `compliance_officer`: same plus escalation read; `tenant_admin`: no extra chat tools (admin is separate API). `as_of` allowed for all, bounded. Output fields filtered by role (no internal chunk ids to the client, already G-04). L0 test iterates every role x tool x forbidden argument.
- Budget inside TTFT p50 2.0 s / p95 3.5 s (ESTIMATE allocation, not measurement; Model Armor and Presidio latency NOT FOUND, ev §4.2, measured in the E4 spikes): auth+principal 30 ms; cache lookup 10; Presidio 50; embed + Model Armor in parallel 300 (hard timeout 500, fail closed); hybrid SQL incl. as-of filter 80 (p95 100); rerank 250 (timeout 700); LLM TTFT 800; first-sentence buffer + numeric gate (about 5 ms) + policy checks 150. Sum about 1.7 s. New code adds under 10 ms; the ingest scan is off the hot path.
- Rejected: LLM detector on the hot path (ADR-009); NeMo (2,057 ms CPU figure UNSUPPORTED but latency class is wrong); per-document ingest screening at 4 MB (whole-document windows lose localisation and hit the token cap); Anthropic Citations API as the numeric gate (cannot combine with structured outputs, ev §4.1); Constitutional Classifiers (no API found).
- Evidence. ev §4.1-4.4, §5 E5; Anthropic docs (untrusted content only in `tool_result`).
- Cost. Model Armor about $0.40 per full ingest pass; chat screening unchanged (free 2M tokens/month is already exceeded by the corpus alone, $0.10/M). Dissent. Security: Model Armor numbers are unmeasured; relying on one managed screen for ingest is risky. Reply: measured in eval set 2 below with a ratchet, plus hidden-text stripping and human review of the flagged list; fallback classifier is a named trigger, not a build.

### 3.9 Advanced RAG and real eval (Track 9)

**D13. Golden set, guardrail sets, arms, pass lines, statistics.**
- Golden set (200 items, Keshav labels, K-R4-4; 40-56 h, ev §1.6 ESTIMATE). Primary-slice quotas: US reg 45 (eCFR + 497K), EU 45 (EN/DE/FR, about 25 cross-lingual query/doc pairs), UK 25, tables 25 (RTS annexes, KID cost tables), temporal as-of 20 (6 state a date), multi-document comparison 15, unanswerable 15, cross-jurisdiction/conflict 5, injection-in-document 5. Publisher-derived items at most 50 (25%). Each item: question, gold answer, evidence span(s) with `bronze_sha256` and `version_key`, answerable flag, slice tags, source-document cluster id. LLM candidates (Haiku batch) + hand-written compliance cases; Keshav checks every item (realistic, span located, answer correct). Two tranches of 100: tranche 1 unblocks the harness and baseline; tranche 2 before any gate that needs 200.
- Storage. `golden.public.jsonl` (public sources only) is committed; `golden.private.jsonl` (publisher-derived) lives in the private bucket, never in the repo or public eval sets (K-R4-3). The eval corpus is frozen by a manifest of `bronze_sha256` values so source updates do not move the gold; a weekly drift job lists items whose evidence span no longer exists in current text.
- Statistics (one method, no bootstrap). Paired design over items. Binary outcome per item per arm; difference d_i in {-1,0,1}. Estimate = mean d. Cluster-robust standard error by source-document cluster (sum d within cluster, standard sandwich form), so correlated items do not fake precision; the evalstats warning against bootstrap at N<100 [PREPRINT] is avoided by not bootstrapping. Effective N after clustering must stay above 100 (K-R4-4) or the arm is reported as directional. Power arithmetic (ESTIMATE): 12% discordant pairs, effective N about 125, SE = sqrt(0.12)/sqrt(125) = 3.1 pp; one-sided 90% lower bound = estimate - 1.28 x 3.1 = estimate - 4.0 pp. So a 5 pp gain has lower bound about +1 pp: this plan can detect gains of about 5 pp or more and nothing smaller, which matches K-R4-4, and means smaller gains are not adopted (D-R4-3). Slices below 30 items (temporal, comparison, unanswerable, conflict, injection) are directional only; no pass line rests on them. Holm correction across arms of the same family. Judge-based metrics gate only if judge-vs-Keshav kappa on 60 labelled items is at least 0.6 (proposed line); otherwise answer-level scores are reported and only deterministic metrics gate. Deterministic metrics first: evidence-span recall@k (span-level gold), citation ID validity, numeric-in-span, validity-interval containment.
- Arms and pass lines (baseline = current ADR-008 pipeline: structure-aware chunks, hybrid+RRF, rerank-2.5-lite, contextual flag OFF, JSON-encoded tool results). "Enter" rule for every arm: estimate at least +5 pp on its named metric, one-sided 90% cluster-robust lower bound above 0, no more than 2 pp loss on any other gated metric, and latency/cost inside budget.

| Arm | Compared with | Metric (set) | Built now? |
|---|---|---|---|
| A1a free structural prefix (title + section path in embedded and FTS text) | baseline | recall@10, 200 items | yes (zero cost) |
| A1b voyage-context-4 | best of baseline/A1a | recall@10 | only if A1a gain is below 5 pp |
| A1c LLM contextual retrieval (Haiku batch, 5.8-8.7x tokens [PREPRINT off-domain]) | best of above | recall@10, cost per 1k docs | last; likely no gain under strong retriever + rerank (Mangla, off-domain [PREPRINT]) |
| A2 temporal filter | no filter | invariant: cited chunk valid at as-of date = 100% (L0); answer accuracy on 20 temporal items = directional | filter ships as correctness (see dissent), arm reports |
| A3 tables | markdown table chunk with repeated header (baseline) vs XBRL fact router | table slice (25) directional | router NOT built unless table slice accuracy is below 70% |
| A4 multi-document | single-shot Haiku decomposition vs plain retrieval | comparison slice (15) directional | NOT built unless baseline comparison accuracy is below 70%; iterative loops excluded by latency (2+ hops cannot meet p50 2.0 s, author estimate, ev §5 E3) |
| A5 cross-lingual | EN query vs DE/FR docs direct vs query translation | recall@10 on the cross-lingual items | translation built only if direct recall is more than 10 pp below EN-EN recall |
| A6 citations | paragraph level (baseline) | deterministic checks only | no sentence-level arm (granularity preprint is off-domain, ev §5 E5) |
| A7 injection | datamarking vs JSON-encode | ASR on indirect set; numeric-gate FPR; golden accuracy | yes, one run |
| A8 reranker pin | rerank-3-lite vs rerank-2.5-lite ("older" in the Voyage table, CORRECTED) | recall@10 non-inferior within 2 pp | yes; tie goes to the model not labelled older (explicit exception to D-R4-3: support lifetime, not quality) |

- Guardrail eval sets (all licence checks re-run on the exact revision at integration, ev §1.7): PII = openpii-1.5m (CC-BY-4.0 per card) 1,500 EN/DE/FR samples + Gretel finance multilingual (Apache-2.0 per metadata, card not re-read) 1,000 + 100 hand-made finance strings (IBAN, account numbers, which ai4privacy lacks); metrics recall/precision per entity class. Direct injection = Lakera gandalf (MIT, 1,000) + deepset (662, licence conflict: smoke only) + 200 benign finance questions from the golden set for false positives. Indirect injection = 500 LLMail-Inject attack strings (MIT) embedded into real chunk windows + 500 untouched corpus windows; metrics: detection recall, window false-positive rate on real regulatory text, and end-to-end ASR through the promptfoo red team. Numeric gate = 300 true cited sentences from golden answers (false-reject rate) + 150 seeded wrong-number sentences (catch rate), includes DE/FR formats and rounding. Pass lines: no external evidence gives absolute thresholds (Prompt Guard recall is on Meta's private benchmark, Model Armor has none), so round 1 measures, then lines are frozen as a ratchet (no regression larger than 2 pp) with these proposed floors: numeric gate false-reject at most 5%, catch at least 90%; quarantine false positives on clean windows at most 1% (reviewed by hand); PII recall at least 95% for person/email/phone/IBAN (proposed, to be replaced by the measured baseline if lower, with the gap recorded).
- Rejected: public QA sets as primary gate (no human-verified US/EU/UK advisor set exists; FinanceBench, FinDER, FinTextQA, EU2UK are NC, ev §1.5); 300 items (+78 h); building every arm up front.
- Evidence. ev §1.5-1.7, §5 E7 (stats protocol is author synthesis), K-R4-4. Cost. Eval runs about $8 each (A6 assumption) x about 10 once = $80 one-off, then about $8/week = about $35/month if weekly runs are kept on the demo tier (set cadence to fortnightly to halve). Dissent. Learning value: skipping A3-A5 builds forgoes a hands-on tour of advanced RAG. Reply: each skipped arm has a numeric trigger and its tickets are pre-written as "conditional"; the brief says a method enters only with measured gain.

### 3.10 Eval-time gating and CI

**D14. Gate split.** CI (every PR, target under 12 min, fixtures only, no network to sources, Anthropic/Voyage stubbed except the pinned L1 smoke): L0 leak matrix extended (documents/versions/ledger tables, wrong-cell), validity invariant, `reconcile_lineage` property tests, deletion-ledger resurrection test, race tests with hooks, quarantine fixture, numeric gate unit corpus, compose two-cell smoke, schema-compat check, model-retirement check, L1 retrieval on the public golden subset with recall regression over 2 pp failing. Weekly (demo environment, real providers): full 200-item golden run incl. private items, guardrail sets, ablation re-runs on change, erasure audit, restore-replay drill, `tenant-move`, cell-down drill, source-drift and reconcile on live sources, license/terms re-check list. Pre-release: full golden gate on demo (the K-R4-4 release gate).

## 4. Edge-case catalogue (brief C.3 plus additions)

| # | Case | Design control | Test that proves it | Cadence |
|---|---|---|---|---|
| 1 | Delete during ingest | Document row lock: indexer takes `FOR SHARE`, eraser `FOR UPDATE`; late chunks of a `deleting` doc dropped to ledger; ledger consulted by connectors | Compose test pauses the indexer after embed, issues delete, resumes: zero chunks remain, ledger has `late_event_dropped` | CI |
| 2 | ACL change during a streaming chat | Every retrieval is a fresh RLS transaction; applier commit bumps `acl_version`; in-flight text already sent is accepted (bounded by one turn, documented) | Stub LLM pauses between tool iterations, ACL change applied, iteration 2 returns no restricted chunk; cache purged | CI |
| 3 | PUBLIC document updated while cached | `corpus_version` in key, `as_of` in key, verifier re-run on hit, purge by `source_document_ids` | Cache an answer, ingest new version, same question: miss or fresh citations; old chunk never cited | CI |
| 4 | Duplicate document in two firms | Uniqueness and bronze path are tenant-scoped; deletion scope is tenant-scoped | Same sha256 in F-EU and F-UK; delete in F-EU; F-UK retrieval unchanged; leak matrix passes | CI |
| 5 | Poison document | Per-document isolation: parse/Pandera failure to `ingest_rejects`, bounded retries, then `quarantined`; consumer continues; DLQ for envelope faults | Corrupt PDF + zip bomb + 200 MB file + injected-instruction file in one batch: batch completes, others indexed, rejects listed | CI (small fixtures), weekly (real) |
| 6 | Partial region outage | Cells share nothing in the data path; wrong/down cell gives 503/403 for its tenants only; directory static | Compose: stop cell-eu; cell-us requests succeed; EU tenant request returns 503 not misrouted; restart recovers | CI smoke; weekly drill |
| 7 | Kafka outage during deletes | Deletes ride Postgres (`deletion_requests` poll), not Kafka; analytics events via outbox later | Stop broker, submit document, advisor and source deletions: all live stores clean, ledger receipts for non-Kafka stores, outbox drains after restart | CI |
| 8 | Replay after a bug fix | `reconcile_lineage` idempotent, honours ledger and quarantine; `parser_version` recorded | Delete a doc, bump parser, replay all partitions: doc stays gone; zero re-embeds for unchanged hashes; chunk counts equal | CI |
| 9 | Clock skew on "as of" | `as_of` from DB `current_date` or validated user date; dates not timestamps; `valid_from` inclusive, `valid_to` exclusive; cache key carries date | Property test over boundaries (day before, on, after); app clock shifted +/-1 day does not change results; user date in future rejected | CI |
| 10 | Model retirement during a demo | Model ids from config; `/readyz` and `demo-up` preflight check models; same-provider fallback if enabled | Stub returns model-not-found mid-run: readiness fails, new turns use fallback or return `LLM_UNAVAILABLE`, no crash; CI retirement check | CI |
| 11 | Late/out-of-order version (older arrives after newer) | `reconcile_lineage` sorts by `valid_from`; metadata-only validity update | Feed versions in all permutations of 4 versions: identical final rows | CI |
| 12 | Source withdrawal, empty/partial listing | Two-strike rule; mass-withdrawal breaker; ledger | Listing stub returns empty: nothing withdrawn, alert; returns 6 of 40 missing twice: held for approval | CI |
| 13 | FCA revocation | `revoke-source fca_api`, connector auto-suspend, in-process path so no Kafka copy | Run on seeded FCA rows: zero rows in Postgres, GCS, BQ ids only; connector refuses to run | CI + quarterly drill |
| 14 | Restore resurrects deleted data | Ledger exported to BigQuery; `replay-ledger` before traffic | Dump, delete, restore dump, replay: gone (compose); cloud restore into scratch instance | CI compose; monthly cloud |
| 15 | Wrong-cell token | 403 `WRONG_CELL`, no data read | Compose: token of EU tenant to US cell | CI |
| 16 | Advisor in two firms | One identity per tenant, one auth instance per tenant in the SPA, tenant-scoped everything | Playwright with two firms, switch firms, no data crossing; same-email-in-two-tenants live test | CI (Playwright), once live |
| 17 | Tenant moves cell | `tenant-move` copy, verify, flip, delete | Compose two cells: move, then reconcile equal, source empty, directory flipped | Weekly |
| 18 | Model Armor quota or skip on ingest | Throttle 300 QPM; `EXECUTION_SKIPPED` = fail closed, retry | Stub returns skipped: status `pending_scan`, not indexed, alert | CI |
| 19 | Injection inside a real document | Hidden-text strip + chunk quarantine + JSON-encode; policy gate on tools | LLMail-Inject windows in a test tenant: quarantined or no tool call executed; red team ASR within ratchet | CI (small), weekly (full) |
| 20 | Numeric gate false reject (DE/FR format, rounding) | Locale-aware normaliser, tolerance table | 300 true sentences false-reject at most 5% | CI unit + weekly full |
| 21 | Re-embed with deletes mid-overlap | Same-row two columns | During backfill delete a document: no `emb_b` row remains; recall gate runs | CI small, weekly |
| 22 | Source terms change (FINRA-type) | Per-document `licence` + weekly terms-URL hash check | Hash change raises an alert ticket | Weekly |

## 5. Failure modes (summary, new parts only)

- Source API down or rate-limited: connector backs off (429/403 stop the run, never loop), `source_state` unchanged, alert after 2 missed runs; chat unaffected (corpus is already indexed).
- Postgres down: unchanged behaviour (arch §7.1). Eraser and ingest wait; deletions are durable as rows.
- Voyage down during reindex/backfill: new hashes stay unembedded (`embedding IS NULL`), reconcile pair 4 alerts; chat unaffected except new content missing.
- Model Armor down at ingest: documents stay `pending_scan` (not indexed). At chat: existing fail-closed.
- 10x load: chat unaffected by new parts except one extra filter; ingest is bounded by source limits (EDGAR 2 rps used of 10) and Voyage (2,000 RPM base; 8M TPM voyage-4); 10x corpus (190k chunks) fits 250k-chunk partition trigger; 100x triggers the existing scale rows.
- Bad input: parser bomb, huge PDF, injection text, wrong language: D12/edge 5/19.
- Data loss: bronze immutable and per-tenant; Postgres backup 7 d; silver and chunks are rebuildable from bronze with `reconcile_lineage` (ESTIMATE minutes at demo size).

## 6. Operating burden and cost summary

| Item | Monthly delta | Note |
|---|---|---|
| Voyage, Model Armor, Haiku (CR arm once) | $0-2 | free tokens cover embeds; CR arm one-off about $10 (ESTIMATE, recompute with Haiku 5.5 batch) |
| Eval runs (weekly full) | about $35 (fortnightly about $17) | assumes $3/$15 Sonnet price, UNVERIFIED |
| Postgres/GCS/backups | $2-4 | 7 d backups, <1 GB |
| Second cell | $0 | local compose only; real cell unpriced, UNVERIFIED |
| Confluent, Langfuse, BigQuery | $0 delta | same plans |
| Total | about $15-40 | inside the $100-200 budget with E10's $110-160 baseline |

Operator burden: new weekly chores = review quarantine list and reconcile report (about 15 min), approve a held mass-withdrawal if one occurs, run erasure audit output check; monthly = restore drill; quarterly = FCA revocation drill and terms re-check. No new on-call surface.

## 7. Impact on epics (existing E0-E10)

| Epic | Tracker / GitHub state | Action | Change |
|---|---|---|---|
| E0 | published, 14 tickets | keep | cell compose skeleton goes to R-CELL, not E0 |
| E1 | published, 21 | update issue text | baseline migration gains `documents` lineage + `document_versions`, `chunks` validity columns and key, `emb_b`, `deletion_requests`, `deletion_ledger`, `source_state`, `documents.lang/licence/attribution/authentic`; RLS and roles for new tables; leak matrix extended |
| E2 | published, 21 | update | Kong per-cell upstream/CORS for `api_base`; otherwise unchanged |
| E3 | published, 16 | update | `as_of` filter in SQL and tool schema, cache key `as_of`, embedding column switch by `embed_gen`, validity invariant test |
| E4 | published 17 of 27 | update (T18+ unpublished: rewrite; T1-T17: acceptance-criteria edits only) | numeric gate, `policy.py`, disclosures, `as_of` plumbing, ROLE_POLICY, grounding metrics |
| E5 | published, 14 | update | `acl-applier` becomes table polling + `eraser` role; topic retention 7 d / segment 1 d; schema compatibility check; Kafka stays for ingest and analytics |
| E6 | unpublished, 19 | rewrite | connectors replace the synthetic-only scope; `reconcile_lineage`; quarantine scan; real PUBLIC path; reconcile job; contracts; per-version Parquet |
| E7 | unpublished, 18 | rewrite | golden set 200 (not 50-300), guardrail sets, arms A1-A8 with triggers, stats module, gate split |
| E8 | unpublished, 12 | update | directory fetch, firm switcher, per-tenant auth instances, `as_of` field, disclosures |
| E9 | unpublished, 17 | update | metrics: reconcile mismatch, quarantine count, numeric-gate rejects, ledger age, source lag |
| E10 | unpublished, 24 | update | 7-day backups, BQ time travel 48 h, soft delete 0, `cell` Terraform module applied once, erasure and restore drills |
| R-DATA (new) "Real data onboarding" | new | new | D1, D2, D3 connectors, manifests, source_state; spikes: FCA API, eCFR terms, CELLAR rate behaviour |
| R-LIFE (new) "Data lifecycle and deletion" | new | new | D4/D5 only if split from E6, D6-D8 eraser, ledger, audit, replay-ledger, drills |
| R-CELL (new) "Regional cells" | new | new | D9 compose two cells, directory, WRONG_CELL, tenant-move, IdP two-tenant test |

Published issue handling (Project #5: 103 issues over E0-E3, E5, and E4 T1-T17; tracker shows every ticket `todo`, so nothing is built): no issue needs closing for being wrong; edits are text updates (E1, E2, E3, E4, E5 acceptance criteria) and new tickets for the new epics. Tickets for E6-E10 and E4 T18+ are rewritten in tracker.json with no publish diff. Ticket count (ESTIMATE): R-DATA 9, R-LIFE 10, R-CELL 7, edits/new inside E1-E10 about 22; all S/M.

## 8. New ADR titles (ADR-026+)

- ADR-026 Source connectors, change capture and the withdrawal safeguards
- ADR-027 Valid-time chunks, version rows and declarative `reconcile_lineage` (no PG18 temporal)
- ADR-028 Deletion pipeline: Postgres-table queue, ledger, retention-bounded slow stores, no crypto-shredding, erasure SLA wording
- ADR-029 Source takedown and FCA revocation runbook
- ADR-030 Regional cells with static directory and client-side routing; residency scope = data at rest
- ADR-031 Data contracts, quality gates and hash reconciliation; OpenLineage dropped
- ADR-032 Blue/green re-embedding with two embedding columns
- ADR-033 Ingest-time injection scan, quarantine and spotlighting stance
- ADR-034 Numeric grounding gate, compliance checks and role policy
- ADR-035 Real golden set, statistics method and ablation pass lines
- Amendments: ADR-008 (as_of filter, reranker pin), ADR-009 (ingest scan), ADR-013 (retention 7 d, deletes off Kafka), ADR-014 (versions, per-version Parquet, PUBLIC path), ADR-015 (as_of in key), ADR-016 (arm A1), ADR-017 (golden 200, gate split), ADR-022 (polling applier).

## 9. Main risks

1. Eval power: effective N may fall near 100 after clustering, making many arms directional; mitigation is slice quotas and "no gain detectable = not adopted".
2. Labelling is 40-56 h of Keshav time (ESTIMATE, unsourced) and gates ablations; tranche 1 of 100 mitigates.
3. FCA API unknowns (format, rate number, revocation, licence conflict, ev §1.3) could void the UK Handbook leg; exit built into ticket 1.
4. Legal status of publisher documents is unresolved (ev §0.3); design keeps them in firm tenants, private, with `licence='unknown'`; counsel review is open.
5. Erasure windows are documented, not measured; wording says so; PITR retention unknown in prod profile.
6. Model Armor performance on regulatory text is unmeasured; ingest could over-quarantine.
7. Residency promise is data-at-rest only; EU/UK users may expect inference residency (ev §0.4). Wording risk, not an engineering one.
8. BigQuery and Langfuse have no local twin, so residency and deletion for those stores are tested only in the cloud demo.
9. PG16 stays (binding arch): if the project later wants PG18 temporal keys, D4 migrates cleanly because validity columns are plain dates.
10. Unverified: Cloud SQL `btree_gist` on PG16 (only needed for the optional EXCLUDE), Kafka retention max on Basic, schema-registry default compatibility, Identity Platform same-email behaviour, Kong path routing across two compose cells (basic feature, still verify in the first R-CELL ticket).

## 10. What this design makes harder later

- Chunk-level system-time audit and retrieval replay (needs `retired_at` and no physical delete, conflicts with erasure).
- Real per-subject erasure proof on backups (needs verified CMEK semantics or a different store).
- Automatic cross-region failover and inference residency (would need EU model endpoints and a real router).
- Sentence-level citations, iterative multi-hop retrieval and an XBRL router are deliberately absent until triggers fire.
- A third-party lineage catalogue (OpenLineage) would be a new integration.
