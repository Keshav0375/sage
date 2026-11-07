OPTIONS

# P-reliability: round 4 stage 2 design (lens: reliability and correctness)

Author: solution-architect (reliability lens), 2026-11-02. Scope: changed parts only (real data, change capture, bitemporal versions, deletion, cells, contracts and reconciliation, re-embedding, guardrails on real data, advanced RAG and eval, edge cases). Evidence tags are those of `evidence-r4.md` (ev §n). Items marked ASSUMPTION or UNVERIFIED are not from evidence; each has a test that settles it. Nothing here is built; no repo edits.

## 0. Lens, assumptions, numbers

Lens: every claim the system makes about correctness is backed by a control that fails closed and a test that proves it. Where a store has a measured deletion window, the SLA states the window, not a wish.

Binding inputs kept: Kong, FastAPI, React/TS, demo multi-tenant (E1), $100-200/month demo-on-demand, Postgres 16 + pgvector 0.8.5 pool tenancy with RLS (ADR-002/003), outbox + Kafka (ADR-013), `acl-applier` (ADR-022), K-R4-1..4, D-R4-1..3.

Assumptions (flag to Keshav if wrong):
- A1 First set size: eCFR 17 CFR 275 (225 KB XML, 39 sections, 143 version records) + 3 fund families x 10-15 497K (~5 MB) + PRIIPs Reg 1286/2014 x 3 versions x EN/DE/FR (9 files, 0.5-1 MB) + RTS 2017/653 + 1 corrigendum + legislation.gov.uk eur/2014/1286 x 3 versions + ESMA/JC Q&A snapshots + FCA COBS 9A/6 (API, current text) + 10-20 ADV brochures (private). Total text about 25-30 MB, about 7M tokens, about 25k child chunks after structure-aware chunking (ASSUMPTION: 4 chars/token, ~400-token children). Versions share unchanged provisions, so chunk rows are far fewer than 3x.
- A2 Peak load stays ~10 QPS, 3 firms + PUBLIC per cell; real people stay synthetic (D-R4-2) but every deletion path is designed for real subjects.
- A3 Text-only residency: model calls are US/global (K-R4-1; ev §0.4).
- A4 Sonnet 5.5 $2/$10 per MTok, Haiku 5.5 $0.10/$0.50, Batch -50% (decisions.md model ADR, ADR-016). Voyage prices from ev §2.5.

Back-of-envelope (arithmetic shown):
- Fetch of the first set: EDGAR cap is 10 req/s (ev §1.1); we run at 2 rps: 45 filings = 23 s. eCFR Pt 275 = 1 GET; CELLAR 9 files; whole set under 2 minutes of network time. Throughput is never the constraint; correctness of change detection is.
- Postgres size: 25k chunks x (2 KB halfvec + 2 KB text + ~1 KB tsv/index) = ~125 MB. At the designed ceiling (2M chunks, ADR-003 trigger) = ~10 GB. Backups, vacuum and restore time scale with this, not with load.
- Initial embed: 25k x 400 tok = 10M tokens x $0.06/M = $0.60 (inside the 200M free tokens, ev §2.5). Re-embed at 100k chunks = 40M tokens = $2.40 ($1.6 batch at 33% off); at 1M chunks = 400M tokens = $24 ($16 batch); time at the documented voyage-4 8M TPM ceiling: 5 min and 50 min. These are ceilings, not measurements (ev §6 gap: no throughput measured). HNSW build time at 100k-1M is unmeasured: spike in E3.
- Per 1k real 497K filings (100 KB HTML ~25k tokens, ev §4.2): embed 26M tokens = $1.6; Model Armor scan at $0.10/M = $2.6; contextual headers (Haiku batch, chunk-only context) ~$3, but whole-document context per chunk uncached = 60 chunks x 26k x 1k docs = 1.56B input tokens x $0.05 = $78. That 26x spread is why contextual retrieval stays an ablation arm, not a default.
- Model Armor free tier 2M tokens (~8 MB, ev §4.4) < first full ingest (~10 MB): overage about $0.05 once, then under $1/month.
- Golden-set statistics: n=200, p=0.8: +/-5.5 pp naive (ev §1.6). Clustered by source document: with ~55 documents (3.6 items each) and an ASSUMED intra-document correlation rho=0.3, design effect = 1 + (3.6-1) x 0.3 = 1.8, so n_eff = 200/1.8 = 111, which clears K-R4-4's "above 100". If rho is 0.5, n_eff = 87 and the clause fails: cap items per document at 6 and require at least 45 distinct documents; compute the real design effect from the labelled set (task in E7).

## 1. Architecture of the changed parts (text diagram)

```
                         GLOBAL CONTROL PLANE (no content, no secrets of tenants)
   Identity Platform (global; tenant per firm) --- signed cells.json (tenant -> cell, residency_class, cell endpoints)
        |                                                   | (read at start + 60 s refresh; static file in GCS + baked fallback)
   SPA (one auth instance per firm) --> resolve cell --> https://<cell>.api  (router = Kong/ALB host rule; cell re-checks)
 ------------------------------------------------------------------------------------------------------------------
  CELL us-central1 (deployed)                              CELL eu/uk (compose only, K-R4-1)   [identical stack]
  chat-api -> principal: tenant.home_cell == this cell?    (else 421 + cell hint, zero DB reads)
  Cloud SQL PG16 (tenants in THIS cell only; PUBLIC; erasure_ledger; source_state; embed_generations)
  GCS bronze/silver/quarantine (soft delete 0)  BigQuery (dataset in cell location, time travel 48 h)
  Confluent Basic + SR (delete-policy topics, retention 7 d)  Langfuse (per-cell account)  KMS keyring (per-tenant KEK)
  fa-worker roles: outbox-relay, silver, contextualizer, indexer, acl-applier, erasure-worker, bq-sink, eval-judge
  jobs: etl (tenant), etl-public (PUBLIC, per cell), reconcile, erasure-verify, embed-backfill, move-tenant, dbt, maintenance
 ------------------------------------------------------------------------------------------------------------------
  Source connectors (inside etl / etl-public):  eCFR | EDGAR | CELLAR | legislation.gov.uk | ESMA | FCA API | private fetch
     -> SourceObservation (append-only, system time) -> listing-diff + feed -> contract + scan -> quarantine OR
     -> document_versions (valid_range x sys range) -> atomic version publish (one tx: chunks + range merge + corpus_version bump)
     -> answer_cache purge by source_document_ids -> events (outbox) -> BigQuery
  Deletion path: request -> erasure_ledger row + tombstone + (Postgres delete) + outbox ErasureRequested
     -> per-store erasure-worker steps (cache, GCS, BQ, Langfuse, Kafka wait) -> erasure-verify (probe + window timers) -> receipt
```

Components that are new: `source_state`/`source_observations`, connectors, `document_versions`, `erasure_ledger` + `erasure_steps`, `erasure-worker`, `erasure-verify`, `reconcile`, `embed_generations` + `embed-backfill`, `move-tenant` job, signed `cells.json`, `policy.py` (role x tool x output), `numeric_gate`, `licence_footer`. Everything else (silver, indexer, applier, chat-api modules) is extended, not replaced.

## 2. Decision R1: first source set, connectors, firm mapping (task 1)

Choice: PUBLIC tenant (per cell) holds public law and public Q&A; firm tenants hold private publisher documents; a `licence_class` field gates what may be quoted. Connectors implement one interface `list() -> [ListingItem]`, `changes(cursor) -> [Observation]`, `fetch(item) -> bytes`, `classify(item) -> {jurisdiction, tier, licence_class, language, authoritative}`.

| Source | Connector, access | Goes to | jurisdiction / tier / licence_class / language | Notes (ev) |
|---|---|---|---|---|
| eCFR 17 CFR 275 (+270 optional) | versioner API, `Accept-Encoding: gzip` (else 406), <= 1 rps (limit UNVERIFIED), `/full/{date}/` per version | PUBLIC | US / 1 / `us_gov` / en | point-in-time native; 9 removed sections = delete case; site is "unofficial" compilation: label non-authentic (ev §1.1) |
| SEC RR datasets (optional) | quarterly zip, 82 MB | PUBLIC (structured table `fund_rr_facts`, not chunks) | US / 1 / `us_gov` | cross-check and the XBRL-lookup ablation arm; "cannot guarantee accuracy" |
| EDGAR 497K | per-CIK submissions JSON + daily-index, UA declared, <= 2 rps | firm tenant (Firm Alpha), private bucket | US / 1-2 / `publisher` / en | no reuse licence found: K-R4-3, never in repo or public eval; avoid 485BPOS (75 MB) |
| ADV brochures | manual list of 10-20 PDFs | firm Alpha, private | US / 2 / `publisher` | same rule; ADV-W not parsed |
| EUR-Lex CELLAR | SPARQL + REST, throttle 1 rps (limits undocumented) | PUBLIC | EU / 1 / `eu_consolidated_ccby` / en, de, fr | per-act version list (43 consolidated versions over 5 acts); label "not authentic"; carry base-act CELEX |
| ESMA Q&A, JC PRIIPs Q&A | weekly hash poll of PDFs + news page | PUBLIC | EU / 1 / `esma_transformed` / en | output footer: "drafted using material downloaded from ESMA's website", non-endorsement |
| legislation.gov.uk | `/update` feed filtered + `hasVersion` + point-in-time XML; 1 rps (fair-use 1,500 per 5 min) | PUBLIC | UK / 1 / `ogl` / en | "(revoked)" = valid_to set, not erased |
| FCA Handbook API (COBS 9A, 6) | API key, current + future only, rate unknown: 1 rps | PUBLIC-UK with `source_class=fca_api` | UK / 1 / `ogl_fca` / en | cl.13 revocation + delete: source class policy `on_withdraw=erase` + kill switch (R3) |
| KIDs (iShares EN+DE, DWS DE) | manual fetch at runtime | firm tenant Firm Beta (EU) | EU / 2 / `publisher` / en, de | tag `regime_date`; PRIIPs KID template reform pending (ev §1.2) |

Firm mapping (3 synthetic firms, matches ADR-002): Alpha = US RIA, advisors `{US}`; Beta = EU wealth manager, advisors `{EU}`; Gamma = cross-border `{US,EU,UK}`. Public law is read by every firm through the PUBLIC partition; publisher documents are tenant rows, so Gamma never sees Alpha's 497K. Tier: statute, rule, Q&A = 1; firm-uploaded publisher disclosures 2; synthetic internal policies 3-4 (existing).

Rejected: FINRA (terms, ev §0.2), EDGAR full-text (403), companyfacts for funds (404, ev §1.1), FCA website crawl (cl.35.3, ev §0.1), putting publisher text in PUBLIC (no licence; PUBLIC is shown to every future tenant). Evidence: ev §1.1-1.4, K-R4-2/3. Cost delta: <$1/month storage + about $0.6 one-off embed. Strongest dissent: skip FCA entirely until written consent (the API is revocable, the licence texts conflict, ev §1.3): the kill switch makes the exposure bounded, but a single UK Handbook purge drill is real work; Keshav's K-R4-2 already chose to include it.

## 3. Decision R2: change capture (task 2)

Choice: one framework for all sources. Each run writes append-only `source_observations(source_id, external_id, version_key, content_sha256, source_ts, observed_at [DB clock], state in {present, revoked, withdrawn, pending})`. Feeds are an accelerator; a periodic full-listing diff is the source of truth for deletes. Cursor and overlap live in `source_state(source_id, cursor jsonb, overlap_s, last_listing_at)`, updated in the same transaction as the observations it covers (Google Changes pattern, ev §2.1).

Rules (every source):
- Idempotent by `(source_id, external_id, version_key, content_sha256)`. Same bytes seen twice = no-op; same version_key with different bytes = `silent_edit` event, a new `document_versions` row with the same valid range and a new system-time range, alert (Airbnb/Airbyte "cursor misses silent edits", ev §2.1).
- Overlap window: every incremental read starts at `cursor - 48 h`; safe because of idempotency.
- Ordering key is the SOURCE's version key, never arrival time. A version older than the current head is accepted and slotted into the valid-time line under a per-document advisory lock (late and out-of-order case, R4).
- Withdrawal needs two consecutive listings that omit the item (a one-off API glitch is not a withdrawal), then `state=withdrawn`. Mass-deletion breaker: if one listing drops > 5 items or > 10% of a source, apply nothing, freeze the connector, page. A listing that returns 0 items is always a failure.
- Then source-class policy decides: `on_withdraw = retire` (set valid_to, keep text for as-of; law, Q&A) or `erase` (physical removal, R5; FCA, publisher docs on request).

| Source | Incremental | Delete / revoke signal | Backstop listing | Cadence |
|---|---|---|---|---|
| eCFR | `titles.json up_to_date_as_of` advances, then diff `versions/title-17.json?part=275` on (identifier, amendment_date, issue_date) | `removed:true` = tombstone (retire); `substantive:false` = metadata-only | full versions list every run | daily |
| EDGAR | per-CIK submissions (new accession, acceptanceDateTime), daily-index | none per filing | Saturday full-index vs last week's set; accession missing = `withdrawn` candidate | daily + weekly |
| CELLAR | SPARQL `cdm:lastModificationDate` poll for 5 acts | in-force flag, end-of-validity date, repeals | list all consolidated CELEX per act, diff | daily |
| legislation.gov.uk | `/update` Publication Log filtered to 3 eur items | title "(revoked)", status | `hasVersion` list per item | daily |
| ESMA / JC Q&A | news page diff + PDF hash | "Deleted" in changes overview (curated `withdrawals.yaml` in repo, human-reviewed) | weekly hash | weekly |
| FCA API | weekly poll of listed modules by hash / last-modified | 401/403 or revocation notice = `purge_source` | module list | weekly + monthly email (manual) |
| private publisher docs | none (manual fetch) | operator `erase` | none | on demand |

`pending` state: legislation.gov.uk "known change, not yet applied" (lag 4-8 weeks, secondary summary, ev §2.1) is stored as `status='known_pending'` on the affected provision; retrieval is unaffected, but the compliance check adds a "known pending amendment" warning (R12).

FCA kill switch: `purge_source('fca_api')` = erase all versions, chunks, bronze, silver, BigQuery rows, cache rows and trace ids derived from that source (found through lineage, R10) with a receipt, runnable in one command and drilled quarterly. Cost delta $0. Rejected: CDC/Debezium on sources (none exposes it), trusting feeds alone (EDGAR removals only visible in the weekly rebuild, ev §2.1). Dissent: listing-diff doubles read volume; at these sizes it is seconds.

## 4. Decision R3: bitemporal versioning (task 3)

Choice: Postgres 16 `daterange` for valid time and `tstzrange` for system time, with `EXCLUDE USING gist` (needs `btree_gist`, available on Cloud SQL, ev §2.2). We do NOT depend on PG18 `WITHOUT OVERLAPS`: that only covers one range dimension, temporal FKs cannot cascade (ev §0.5), and Cloud SQL's PG18 default vs our pinned PG16 is not a reason to move. Upgrading to PG18 is a later, separate ADR.

```
documents (logical, per tenant): doc_key = source_id + external_id, language, jurisdiction, tier_required, licence_class,
                                 attribution_text, authoritative bool, source_class
document_versions: version_id, doc_id, version_key, valid_range daterange, sys_range tstzrange [DB clock_timestamp],
    bronze_sha256, content_hash, status in {ingesting, active, superseded, revoked, withdrawn, quarantined, known_pending, erased}
    EXCLUDE USING gist (tenant_id WITH =, doc_id WITH =, valid_range WITH &&) WHERE (upper_inf(sys_range))
chunks: + version_first_id, version_last_id, provision_path, language, valid_range daterange (derived), embed_generation
    identity = (tenant_id, doc_id, provision_path, chunk_hash, embed_model); is_current generated = upper_inf(valid_range)
```
- Valid time = when the text was in force (eCFR amendment_date, CELEX date suffix, legislation point-in-time date, 497K filing date; KID: "accurate as at"). System time = when we learned it. One current belief per (doc, valid time); older beliefs are closed (`sys_range` upper set), never overwritten, so any past answer is reproducible by `known_at`.
- Chunk range merge at version publish: for each provision path, same `chunk_hash` as the previous version => extend `valid_range` (no embed call; Notion hash pattern, ev §2.1); changed => close the old chunk at the new valid_from and insert a new one; provision removed => close. Result: embeds scale with changed provisions, not versions x provisions.
- As-of query: `valid_range @> $as_of::date` in the one retrieval SQL (ADR-008 statement). `$as_of` is set server-side: an explicit date or year found in the question by a deterministic parser (the model never sets it), else the UI chip value, else `current_date` read from Postgres inside the transaction. Half-open ranges `[from, to)`; dates are UTC calendar days. System-time queries (`known_at`) exist for admin, audit and eval only.
- Defence in depth: RLS is isolation, not time. A forgotten `as_of` predicate would give a stale answer, not a leak, so a second independent check runs after generation: every cited chunk's `valid_range @> as_of` (R12). CI test: every SQL string in the retrieval module contains the predicate.
- Cache key adds `as_of` date, `embed_model` and the PUBLIC `source_epoch`; any version publish, supersede, retire, withdraw or erase bumps the tenant's `corpus_version` in the same transaction and deletes `answer_cache` rows whose `source_document_ids` contain the document (GIN exists, §5.5). Hit-time re-verification stays (ADR-015).
- Index: one HNSW per partition as today. Superseded rows are post-filtered by iterative scan (pgvector 0.8, ev §2.2: no guarantee of full recall). E3 spike: build a partition with 30% superseded rows and measure recall@10 and p95 vs current-only; behaviour under RLS plus LIST partitions is an open evidence gap. Trigger for a partial index `WHERE is_current` (default path): recall or p95 miss.
- Subject data (conversations, messages) is NOT bitemporal: it is plain rows so erasure stays physical. Bitemporality applies to the corpus only; this resolves the XTDB-vs-erasure conflict (ev §2.2).

Evidence: PG18 docs, Cloud SQL extensions (ev §2.2); FiscalQA Pro direction only [PREPRINT] (ev §E2); legislation.gov.uk per-provision commencement (ev §2.2). Rejected: PG18 temporal PK/FK; XTDB (no erasure, budget); versioning by overwriting `documents.status` (cannot answer "as of"). Cost: $0. Dissent (simplicity): store only current text; as-of questions are rare. Counter: the first real UK/US/EU corpus has exactly the versions that make "as of" a real compliance question, and it is the only way to represent "revoked".

## 5. Decision R4: atomic publish, tombstones, races (task 2/4 glue)

- The indexer is the only writer of chunks. It embeds first (outside any transaction), then ONE transaction: take `pg_advisory_xact_lock(hash(tenant_id, doc_id))`, check `NOT EXISTS tombstone(doc_id/version_key)` and `contract_passed AND scan_passed`, insert/extend chunks, set the version `active`, bump `corpus_version`, purge cache rows, write `processed_events`. A chunk existing in the table therefore means the version passed every gate; Dagster blocking checks are advisory only (their behaviour across runs is undocumented, ev §2.2).
- Erasure and withdrawal take the same advisory lock and insert the tombstone first. Delete-during-ingest therefore has two outcomes only: the indexer wins the lock (rows exist, erasure then deletes them) or erasure wins (indexer sees the tombstone and writes nothing). The silver worker checks the tombstone before and after writing Parquet and deletes its own output if a tombstone appeared.
- Every sink (bq-sink, silver, contextualizer, indexer) consults the tombstone set (cached 60 s, table-backed, consumer pauses if it cannot read it) before writing, so a Kafka replay after a bug fix cannot resurrect erased data.
- Reconciler invariant "tombstone implies absence everywhere" (R10) is the net under all of this; `tombstone_violations_total` must be 0.

## 6. Decision R5: deletion everywhere (task 4)

Taxonomy: (S) source withdrawal (retire or erase per source class), (D) data-subject erasure (advisor, conversations), (T) tenant offboarding or move, (X) source kill switch (FCA/publisher). Physical delete is the mechanism for every LIVE store; crypto-shredding is used only where physical delete is impossible or slow (immutable and append-only stores), and per-subject KMS keys are NOT adopted (see rejected).

| Store | Mechanism | Window after request (ev §2.3) | Config we set | Proof step |
|---|---|---|---|---|
| Postgres live (docs, versions, chunks, conversations, messages, feedback, eval_scores, turn_events, answer_cache) | explicit ordered DELETE in one transaction by `erasure-worker`, row counts recorded; then `VACUUM` of the affected partitions (dead tuples and HNSW entries) | live rows immediate; dead tuples until vacuum (target < 24 h) | none | count = 0 queries; ANN self-probe cannot return it |
| Postgres backups / PITR | no per-row purge exists (ev §2.3); residual window = backup retention | up to backup retention | automated backup retention 7 days; PITR log retention set explicitly (days UNVERIFIED, confirm in console); no on-demand backups kept | restore drill: restore to scratch, replay ledger, assert counts 0 |
| GCS bronze/silver/quarantine | delete by generation; subject-data buckets must not use retention lock | immediate if soft delete = 0; else 7 d (range 7-90, cannot purge early) | `soft_delete_policy` 0 on the data bucket, versioning off (bronze is content-addressed and re-fetchable except for exactly the withdrawn documents) | `list` with generations shows none |
| Parquet silver | object delete per partition file; silver is per document file (not per day) so one document = deletable files | same as GCS | silver path `silver/tenant_id=/doc_id=/version=` | list is empty |
| BigQuery | one batched DML `DELETE ... WHERE subject_ref IN UNNEST(@refs)` hourly, only for refs older than 30 min (avoids the streaming-buffer limit, ev §2.3); 2 concurrent + 20 queued DML per table respected | 9-14 d (time travel 2-7 d + fail-safe 7 d fixed) | dataset `max_time_travel_hours = 48` => window 9 d | count = 0 now; at T+9 d `FOR SYSTEM_TIME AS OF` probe is rejected or empty |
| Kafka (Confluent Basic) | subject-bearing topics are delete-policy (no compaction), `retention.ms` 7 d, `segment.ms` 1 d if editable (low volume means segments roll by time: UNVERIFIED, test); tombstone only on compacted entity topics (none planned) | <= retention + segment roll (8 d if segment.ms editable, else up to 14 d); compaction route would be >= 7 d + cleaner (ev §2.3) | payloads minimised to `subject_ref`/ids, never text beyond redacted | verifier consumer scans retained segments for `subject_ref` at T+8-14 d |
| Schema Registry | n/a (schemas only, no subject data) | n/a | n/a | n/a |
| Langfuse Cloud (synthetic only; self-host for real data, §1.3) | `messages.trace_id` stored; batch DELETE by trace id; sessions have no delete endpoint | "usually within 15 min", no guarantee, no confirmation (ev §2.3) | never copy production traces into datasets; nightly job deletes traces older than 30 d (retention is Pro-only) | GET trace after 30 min = 404, retry, alert at 24 h |
| Cloud Logging | keep subject text out; logs carry `subject_ref` only; no per-entry delete exists (ev §2.3) | custom retention | `_Default` retention 7 d | log query for the ref after 7 d = none |
| Valkey | Kong counters only (no content) | n/a | n/a | n/a |
| Model providers (Anthropic, Voyage) | not controllable; Voyage ZDR opt-out exists, Anthropic Batch is not ZDR-eligible (ev §2.5, §3.1) | provider terms | use ZDR where offered | stated as out of scope in the SLA |

Crypto-shredding scope: GCS and Kafka payloads may carry a per-TENANT KEK (3 keys x $0.06/month = $0.18, ev §2.3) for tenant offboarding: destroying the KEK (24 h minimum scheduled destruction, ev §2.3) makes bronze/silver copies in backups unrecoverable. For subject-level erasure the unit is the physical delete plus unlinking: events, BigQuery rows, traces and logs carry `advisors.pseudonym_id` (random uuid), never `idp_uid` or email; erasing an advisor deletes the mapping row immediately, so surviving analytics rows become unlinkable at once while physical deletion runs inside the windows above. Honest limit: Presidio recall is unmeasured, so redacted free text may still contain PII; unlinking alone is NOT claimed as erasure (Spotify rejected tokenization for the same reason, ev §2.3).

Ledger replay (the control that makes backup retention safe): `erasure_ledger` stores only `(request_id, scope_type, salted_hash(subject or doc id), requested_at)`. It is also exported daily to an append-only GCS object. After ANY restore (PITR, backup, move target) `erasure-replay` re-applies it before traffic is allowed, so a restore cannot resurrect erased data; retention then only bounds residual bytes in backup media.

Legal hold: `escalations`, audit rows and records a regulator may require carry `retention_class`. An erasure request returns "retained: legal basis X" for them in the receipt (policy for counsel to confirm).

Honest erasure SLA wording (draft for Keshav; replace numbers with canary measurements, R10):
"Within 24 hours of a verified request we remove the data from the live system: database, search index, answer cache, document store and trace store. Analytics copies in the warehouse and event streams are removed within 14 days (warehouse recovery windows are 9 days after deletion; event topics keep data up to 7 days plus a segment roll). Backups expire within 7 days and any restore re-applies your erasure first. Model providers process requests under their own retention terms and are outside this guarantee. Text already shown to an advisor, and records we must keep by law, are not recalled. After every window has closed you receive a receipt listing what was removed from each store and how it was checked."

Evidence: ev §2.3 (all windows), ev §3.1 (providers). Rejected: per-subject KMS keys ($0.72/key/year = $17/month at 300 advisors, $120/month at the 2,000-advisor design, 100 write TPM quota, destroyed-key effect on standard backups undocumented); crypto-shredding the live index (encrypting vectors defeats pgvector, ev §2.3); relying on BigQuery AEAD shredding (undocumented); GCS retention lock; Kafka compaction as the erasure path (>= 7 d + cleaner). Cost delta: ~$1/month (KEKs, 7 d backups, scratch restore drill monthly ~$1-2). Strongest dissent: a 14-day outer bound is a long tail; alternative is keeping NO subject-linked rows in BigQuery (aggregates only), which would make the SLA 24 h. We can adopt that later at the cost of per-conversation audit queries; the ADR records it as the lever.

## 7. Decision R6: proof of deletion (task 4)

- Receipt in two phases. Phase 1 "executed" (hours): per-store rows from `erasure_steps(request_id, store, status, executed_at, rows_affected, probe_result)`. Phase 2 "windows closed" (T+9 to T+14 d): `erasure-verify` runs the probes in the table above after each store's window timer, then signs the JSON receipt (HMAC with a KMS key; the receipt is stored in GCS and hashed in the ledger). A receipt never says "erased everywhere" before phase 2.
- Scope resolver = lineage: `lineage_edges(run_id, in_ref, out_ref, stage, parser_version, ts)` links bronze sha256 -> version_id -> chunk_hash -> embed generation -> cited in messages (`retrieval_chunk_ids`) -> BigQuery events. "Find everything derived from X" is a query, not a checklist. Own table, OpenLineage-shaped JSON; `dagster-openlineage 0.2.1` is pinned and optional because it stalled for five months (ev §2.2), and lineage is never a gate.
- Canary drill (measures the real windows; ev §2.3 notes none were ever measured end to end): weekly, a synthetic canary advisor with unique tokens is driven through chat, trace, events and BigQuery in the cloud profile, erased, and the time each store reaches zero is recorded; compose runs the same drill nightly minus provider windows. The published SLA numbers are the maxima of the last 12 canaries.
- Reconciler invariant: tombstone implies absence in Postgres, GCS, BigQuery (current), Langfuse and cache; hourly for 24 h after any erasure, then daily.
Evidence: ev §2.3 hidden-assumption note ("erased within N days is a max over systems"). Cost: ~$1/month. Dissent: canary in cloud costs a few cents and a Langfuse account slot; the alternative is a documented, unmeasured SLA, which is what ev §0.5 warns against.

## 8. Decision R7: regional cells, multiple logins, moves (task 5)

Choice: cell = the whole data plane of one region. Control plane = a signed static `cells.json` (tenant slug, tenant_id, `home_cell`, `residency_class` in {none, eu_only, uk_only}, endpoints) plus Identity Platform; no database in the control plane (no new SPOF, no new bill). It changes only through the move protocol or onboarding. Every cell loads it, but its own database physically holds only its own tenants' rows, so a routing bug cannot read another region's tenant: `principal` checks `home_cell == this cell` and returns 421 plus a cell hint without any DB read otherwise.

Per cell (everything): Cloud Run services, Cloud SQL, GCS bucket, BigQuery dataset (location per cell; the EU multi-region excludes London, so a UK cell uses regional europe-west2, ev §3.1), Confluent cluster plus Schema Registry (the registry region is fixed by the first cluster, ADR-013), Langfuse account (US Oregon vs EU Ireland, separate accounts, ev §3.1), KMS keyring, Model Armor regional endpoint. NOT shared: no Kafka cluster links (destination must be Dedicated/Enterprise, ev §3.1), no replication, no cross-region queries (BigQuery errors on cross-location joins, ev §3.1). The PUBLIC corpus is ingested independently in each cell by its own `etl-public`; a manifest comparison (document count + `chunk_set_hash` per version) across cells alerts on drift. This costs about $1 of duplicate embedding per cell and removes every cross-cell data flow.

Global data (declared in the privacy notice, Slack/WorkOS pattern, ev §3.4): user id, email, firm membership, tenant to cell map, PUBLIC manifest hashes, aggregate metrics without tenant text. Must not leave a cell: firm documents and chunks and embeddings, conversations, traces, BigQuery audit rows, eval results of that cell.

Model calls: prompts (redacted question + redacted chunks) go to Anthropic and Voyage, US/global (K-R4-1; inference_geo only global|us, ev §0.4). Control: a cell declares `llm_regions`; a tenant with `residency_class=eu_only` in a cell whose `llm_regions` lacks the EU gets its private documents excluded from retrieval by a deterministic filter (fail closed with a refusal reason) unless Keshav accepts the wording. PUBLIC law is unaffected. Claude on Vertex EU stays a costed option (UNVERIFIED availability, ev §3.1).

Routing: SPA calls `GET /resolve?slug=` (served from the same signed file by any edge function or Kong route) then talks to `<cell>.api`. Cloud Run on a global ALB routes by latency, has no automatic cross-region failover and needs LB host rules for tenant pinning (ev §3.1); host-based per-cell hostnames avoid depending on header routing (UNVERIFIED).

Multiple logins (one advisor in several firms): one Identity Platform tenant per firm (user silos, ev §3.2), one `advisors` row per `(tenant_id, idp_uid)`, one token per firm, no identity merge across firms. The SPA keeps one auth instance per firm (currentUser does not switch with tenantId, and tenantId is not persisted on reload, ev §3.2) and a firm switcher; each API call carries exactly one firm's token. The server verifies at project level, reads `firebase.tenant`, checks it equals the tenant in the URL and the cell map. Gate before E1: the 5-minute test "same email in two tenants" (ev §0 open item). If it fails, onboarding uses per-firm email aliases in the demo and the ADR says so. Linking the same person across firms is an optional, opt-in UX feature, never an authorization input.

Moves:
- Advisor jurisdiction/tier change: `UPDATE advisors` + `entitlement_version` bump; effective for new turns within 60 s (existing TTL). In-flight turn: re-read `entitlement_version` before each retrieval/tool step and before `done`; a bump aborts with `error ENTITLEMENT_CHANGED`, message `refused`. Text already streamed cannot be recalled; the exposure is bounded by one answer (p95 8 s). Documented, tested with a slow fake LLM.
- Document reclassification: ADR-022 unchanged (metadata UPDATE, acl_version bump, cache purge) plus tombstone-style lock so it cannot race an ingest.
- Firm moves cell (copy, verify, cutover, erase; Atlassian pattern, ev §3.4): states `active -> freezing -> copying -> verifying -> cutover -> draining -> source_erased`. Freeze = chat disabled for that tenant (minutes at demo size) and outbox drained to 0. Copy = ordered per-table `COPY` of that tenant's rows into the target cell (same `tenant_id`, embeddings copied as-is, same `embed_model`), GCS prefix copy, BigQuery export/load. Verify = row counts + per-table `md5(string_agg(id||hash ORDER BY id))` equal. Cutover = publish a new signed `cells.json` (atomic). Source tenant row becomes `moved` (421), erased after a 7-day grace through class T with receipt. Failure before cutover = unfreeze source, delete partial target rows (re-online first, then delete, per Atlassian). Langfuse traces do not move (deleted at source, target starts clean; stated).
- Person moves firm: no data transfer; each firm erases under its own policy.

Local two-cell compose (`docker-compose.cells.yml`): networks `cell-us` and `cell-eu`, each with its own Postgres (pgvector image pinned to the Cloud SQL version), Kafka KRaft container, schema registry, GCS stand-in, BigQuery stand-in as the existing compose, Langfuse stub; one `router` container serving `cells.json`; services in one cell cannot resolve the other cell (separate networks; a test proves it). About 4-6 GB RAM (ASSUMPTION, measure). Tests: misrouted token => 421 and zero DB reads in the wrong cell; kill the EU cell => US tenants unaffected; move-tenant success and mid-copy kill; PUBLIC manifest equality; same email in two firm tenants (mock IdP). Real second region cost: a costed ADR option; ev §3.3 says the delta cannot be stated from verified prices. ESTIMATE only: an on-demand second cell (Cloud SQL stopped when idle, UNVERIFIED) adds storage plus run hours, about $15-40/month while used; a standing second cell about $90-150/month, dominated by Cloud SQL (ESTIMATE, UNVERIFIED).

Evidence: ev §3.1-3.4; AWS cell-based (thin router, cell migration "from day one", ev §3.4). Rejected: one global database (breaks residency and blast radius); global Cloud SQL replicas (cross-region replica on Enterprise edition not documented, ev §3.1); a control-plane database (extra Cloud SQL for 50 rows); Confluent cluster linking (Dedicated required); hash-mod partition routing (cannot pin a region, ev §3.4). Cost delta now: $0 deployed. Strongest dissent (simplicity): the full cell machinery for one deployed region is speculative; counter: K-R4-1 asks for designed and locally tested cells, and `tenants.cell_id`, the 421 check and the move protocol are the only code that exists in the one-region deploy.

## 9. Decision R8: contracts, quality, lineage, reconciliation, backfill (task 6)

Contracts (code, versioned): Pydantic models -> JSON Schema in Schema Registry, BACKWARD compatibility, CI check (ADR-013); the `SourceObservation`, `docs.*`, `chunks.*`, `erasure.requested.v1` events are contracts. dbt gold models carry `contract: enforced` where the materialization supports it (tables, not views/snapshots, ev §2.2). Pandera 0.35.0 on silver with `PANDERA_VALIDATION_DEPTH=SCHEMA_AND_DATA` set explicitly (LazyFrame validates schema only by default, ev §2.2) and polars >= 1.20; a planted bad row must fail (CI test).

Blocking quality rules (a failure = `quarantined`, never indexed): licence_class and attribution non-null; jurisdiction and tier non-null; eCFR part has the expected section ids (39 for Pt 275 +/- the version's removals); every CELEX arrives with all three languages or none (partial language sets are quarantined); every 497K has a recognisable fee table or is `parse_incomplete`; chunk token bounds; no empty provision_path; scan passed (R11). Source-level circuit: > 5% of a batch quarantined pauses the connector.

Reconciliation, exact equality (the pipeline is deterministic for a fixed `parser_version`): job `reconcile`, hourly on ingest days, daily otherwise, compares only versions idle > 30 min.

| Pair | Check | Alert |
|---|---|---|
| source -> bronze | every `present` observation has a GCS object whose sha256 metadata equals the observation | ticket after 2 runs |
| bronze -> silver | `n_chunks` and `chunk_set_hash = sha256(sorted(chunk_hash))` per version equal | ticket |
| silver -> Postgres chunks | same count and hash recomputed from `chunks`; every child has embedding NOT NULL and `embed_model = active generation` | ticket |
| index | ANN self-hit canary: 50 sampled chunks queried with their own vectors must return themselves in top-5, `ann_selfhit_rate >= 0.99` (detects a broken HNSW or dimension drift) | page if < 0.95 |
| Postgres -> BigQuery | per day `count` and `md5(string_agg(event_id ORDER BY event_id))` of outbox published rows vs `ingest_events` | ticket |
| cell vs cell | PUBLIC manifest (doc count + chunk_set_hash per version) equal | ticket |
| tombstones | absence in every store (R6) | page |

Backfill and replay during live traffic: a backfill/replay re-publishes `docs.bronze.v1` for a partition; writes are idempotent (`(tenant_id, chunk_hash, embed_model)` unique, `processed_events`), publish is atomic per version (R4), the backfill's Voyage client has its own semaphore capped at 25% of the RPM limit so chat embeds are never starved, and sinks honour tombstones. Test: replay the fixture corpus twice after a parser bugfix; end state hash equals a single run; zero duplicates; zero resurrected tombstones.

Evidence: ev §2.2 (Pandera/dbt/Dagster facts), §2.1 (Notion hash pattern), ev §2.5 (Voyage limits). Rejected: Great Expectations (not evaluated, ev §6), making OpenLineage a gate. Cost: <$1. Dissent: exact-equality reconciliation is brittle across a parser change; mitigation: the comparison is keyed on `parser_version`, so a bump produces a planned re-baseline event, not an alert storm.

## 10. Decision R9: re-embedding blue/green (task 7)

Choice: embedding generations as rows, not columns. `chunks` is already unique on `(tenant_id, chunk_hash, embed_model)`, so a green generation is a second set of rows with the new `embed_model` beside blue. `embed_generations(model_id, status in {building, validating, active, retired})`, `tenants.active_embed_model`.
1. Build: `embed-backfill` job embeds every distinct chunk content with the new model (Voyage batch: 33% off, 12 h window, <= 100K inputs, ev §2.5) into green rows (parents copied).
2. Dual write: while building, the indexer writes both generations; erasure and withdrawal delete by `doc_id`, so they hit both (hard deletes mid-migration, ev §2.4).
3. Validate: counts and `chunk_set_hash` equal per version; ANN self-hit >= 0.99; L1 recall@10 on the 200-set non-inferior (paired, lower bound of the difference >= -2 pp) and retrieval p95 <= +20%.
4. Cutover per tenant: flip `active_embed_model` (instant) for the `eval` tenant first, then others; cache key includes `embed_model`; `corpus_version` bumps. Queries inline the model literal from an allow-list so the per-model partial HNSW (`WHERE kind='child' AND embed_model='...'`) is used.
5. Keep blue 7 days (rollback = flip back), then physical drop of blue rows, then VACUUM; the drop is an erasure-class operation with counts.
Cost/time: see section 0 ($2.4 and 5 min at 100k; $24 and 50 min at 1M, ceilings). Memory: two generations double HNSW size during overlap (1M chunks x ~3 KB x 2 = 6 GB against an 8 GiB instance, so 1M is outside the designed envelope; 250k per tenant is fine). Evidence: Notion generations, practitioner pattern (single-author, ev §2.4). Rejected: in-place `UPDATE embedding` (no rollback, mixed-model space), a second index service (new vendor). Dissent: duplicating parents wastes rows; a shared-parent design saves 40% rows but couples generations. Cost delta $0/month steady.

## 11. Decision R10: guardrails on real data (task 8)

Layers (none is trusted alone: detectors miss, so the structure also limits what an injected instruction can do):
1. Ingest scan. (a) Parse-time sanitiser: drop script/style, comments, `display:none`/off-screen/aria-hidden text, zero-width and bidi characters, long base64 runs; keep a diff count per document. (b) Deterministic pattern list (instruction-override phrases, role markers, tool-call syntax, URLs outside an allow-list). (c) Model Armor document screening per document windowed under the 65,536-token PI limit and the 4 MB file cap; `EXECUTION_SKIPPED` (also on modality mismatch and inputs under three words) = fail closed = quarantine; own throttle <= 300 QPM of the shared 1,200 QPM project quota (ev §4.2). (d) Prompt Guard 2 22M windows and an InjecGuard-class classifier are ablation arms only (Llama 4 licence, manual gate, CPU latency NOT FOUND, ev §4.1; regulatory text contains "ignore", "must", "instruction": over-defense risk, ev §4.2).
2. Quarantine: version `status=quarantined`, bytes under `quarantine/` (never silver), operator `release|reject` recorded; chunks are never written (R4 gate).
3. Query-time structure (unchanged ADR-009): untrusted text only inside a JSON-encoded `tool_result`, tool arguments never carry tenant/tier/jurisdiction/as_of, escalate uses server-side licences. Add a per-request random boundary nonce around chunk text. Spotlighting: delimiting alone only halves attack success and its authors do not recommend it; datamarking is the paper's minimum recommendation but it is a 2023 GPT-3.5/GPT-4 result without Claude and with payload bypasses (ev §4.2). Decision: JSON-encode + nonce by default; datamarking is ablation arm A-INJ-2, applied to the model-visible copy only; the citation verifier and numeric gate always compare against the ORIGINAL chunk text fetched by id, with the marker stripped from any quote before comparison. This sidesteps the worry that the marker breaks the numeric regex and DE/FR formats (the marker replaces whitespace, numbers such as `1.234,56` stay intact), and the arm measures it.
4. Numeric grounding gate (deterministic, per sentence, before release). Extract numbers and dates with locale-aware patterns (EN `1,234.56`; DE/FR `1.234,56`, `1 234,56` incl. narrow no-break space; percent, bps, currency; ISO and long dates in EN/DE/FR) into `(Decimal, unit)`. Each must appear in a cited span of THAT sentence's `[n]`, with rules: rounding allowed only to the precision the answer states (half unit of the last digit), bps<->% whitelisted, identifiers (CELEX, article numbers, `2014/65/EU`, rule numbers) excluded by pattern, the as-of date exempt, derived figures only from a deterministic `calc` tool whose inputs are themselves grounded. A sentence with a number and no `[n]`, or an ungrounded number, withholds that answer with "figure X not found in cited sources" and an escalate offer (counted, reasons enumerated). No paper tests a plain regex gate (ev §E5); FiscalQA scores with regex/tolerance as precedent; FinGround is [PREPRINT] on the authors' data. Hence we measure our own false-reject rate (pass line below). Latency: regex + Decimal, estimate < 10 ms per answer, measure.
5. Deterministic compliance checks (code, each with a test): (a) `licence_footer`: from `document_versions.attribution_text` per cited licence_class: ESMA transformed-text disclaimer + non-endorsement, EUR-Lex "consolidated text, not authentic, only the OJ is authentic" + CC BY indicate-changes line, OGL attribution, "(c) FCA" for FCA, `publisher` = quote cap (default 40 words) + attribution; missing footer blocks release. (b) Jurisdiction: cited sources in the advisor's jurisdictions (RLS) AND label each citation chip with jurisdiction; mixed-jurisdiction answers must carry a warning (UK vs EU PRIIPs). (c) As-of validity: every cited chunk `valid_range @> as_of`, else block. (d) Staleness: existing 12-month rule for firm documents; for law texts the warning is about state (`superseded`, `revoked`, `known_pending`), not age. (e) Suitability and escalation checks unchanged.
6. Role policy as data: `policy.py` table role x tool x output field, default deny. Advisor tools: search, factsheet, lookup_suitability_rule, calc, escalate. compliance_officer adds quarantine summary (never raw quarantined text) and full excerpt of tenant docs; tenant_admin has no LLM tools (admin is API only). Output policy fields: quote cap, show_raw_excerpt, include internal notes. The role x tool matrix test is generated from the table, and a tool without a policy row fails CI.
7. Metrics and budget: per guardrail counters `guard_hits_total{guard,reason}`, `guard_latency_ms`, `guard_skipped_total`, `quarantined_total`, `numeric_gate_reject_total{reason}`; precision, recall and latency per guardrail measured weekly on the eval sets of section 12. TTFT budget (ESTIMATE, to be measured; p50/p95): Model Armor prompt screen runs parallel to embed, critical path = max(embed 0.15/0.25 s, screen X) with X unknown (latency NOT FOUND, ev §0.10), so its fail-closed timeout is set from the measured p99 + margin, not 500 ms by default; first-stage SQL 0.15/0.30; rerank 0.35/0.70; LLM first token 0.8/1.2; sentence buffer + numeric gate + verifier 0.1/0.15. Sum p50 ~1.55 s, p95 ~2.6 s against 2.0/3.5. Rule: any guard adding > 150 ms p95 to the critical path moves to async-after-first-sentence or is dropped.
Evidence: ev §4 throughout; ADR-009. Rejected: NeMo (latency, ev §4.1), LLM detectors on the hot path (ADR-009), trusting the Anthropic 13.8 -> 1.9 chart (UNSUPPORTED, ev §0 open item). Cost: Model Armor < $1/month; no new services. Dissent: ingest-time scanning of trusted public law adds false-positive quarantines for little threat (EUR-Lex/eCFR are not attacker-controlled); counter: publisher PDFs and FCA/ESMA content are third-party, the scan is cheap, and the eval needs the quarantine path exercised on real text.

## 12. Decision R11: advanced RAG, golden set, ablations, statistics (task 9)

Golden set, 200 items (K-R4-4), primary slice partition (sums to 200): single-hop US 25 / EU 25 / UK 15 = 65; tables and fee numbers 25; temporal as-of, superseded, revoked 30 (20 with explicit date, 10 implicit); multi-document, cross-jurisdiction, multi-hop 20; cross-lingual (EN question over DE/FR text, DE question) 20; unanswerable, out-of-scope and ACL refusal 20; injection-in-document (planted in private copies of real text) 10; compliance-check items (footers, stale, escalate) 10. Each item stores question, gold answer, evidence span (document, version, provision path, char offsets), source hash, answerability, jurisdiction, language, slice, `private` flag. At most 6 items per source document, at least 45 distinct documents. Public slice (about 165 items from eCFR, EUR-Lex, legislation.gov.uk, ESMA) is committed with attribution; the private slice (about 35 items from 497K, KIDs, ADV) lives in the private bucket and runs only where it is mounted (K-R4-3). Method: LLM candidate generation (Ragas-style, candidates only), Keshav checks every item (question realistic, span located, gold correct, answerable or not): about 39-56 h (ESTIMATE, ev §1.6). Staged: tranche 1 = 60 items (becomes the PR subset), tranche 2 = 140. Intra-rater check: Keshav relabels 15% after one week; agreement >= 0.8 or the labelling guide is revised (no second reviewer exists).

Metric tiers: Tier-1 deterministic, no judge: evidence-span-in-top-k (recall@10, MRR), gold-version-in-top-5, cited-id exists, numeric-in-span, footer present, ASR by canary string/tool call. Tier-2 judged (Haiku 5.5, calibrated on 60 human labels by PPI): faithfulness, relevance; used as a gate only if judge-human rho^2 >= 0.4 (below 0.2 unusable, evalstats [PREPRINT]); FinRegQA-EU warns judges reward citation density, so citation quality stays deterministic (ev §4.2).

Baseline B0 = current pipeline: structure-aware chunks with free structural prefix (title + section path), hybrid RRF + rerank, hard `as_of` filter for explicit dates, JSON-encode + nonce, deterministic gates.

| Arm | Change vs B0 | Slice / metric | Pass line (D-R4-3, K-R4-4) | Guard |
|---|---|---|---|---|
| A1 context-v | voyage-context-4 embeddings (no LLM call, $0.12/M, ev §E6) | all 200; recall@10 | point gain >= +5 pp, sign test over documents p<0.05 (Holm) | ingest tokens, p95 |
| A2 context-LLM | Haiku batch headers (ADR-016) | all 200; recall@10 | same; plus ingest cost <= $25 per 25k chunks | Mangla predicts little under a strong retriever (off-domain, ev §E6): expected NOT to pass |
| A3 temporal-default | as_of filter also for undated questions (default = today) vs current-version-only | temporal 30; gold-version-in-top-5 | +5 pp and exact McNemar p<0.05 | direction solid (FiscalQA, ev §E2), magnitude not transferable |
| A4 table-router | deterministic `fund_rr_facts` lookup vs table chunks with repeated headers | tables 25; numeric match with tolerance | +5 pp and discordant pairs >= 6 vs 0 (n=25 cannot show less) | Docling TEDS spot check on 20 KID cost tables |
| A5 decomposition | single-shot Haiku split, parallel retrieval, one generation | multi-doc 20; all-gold-spans coverage | +5 pp and p50 TTFT <= +0.4 s | no iterative loops (ev §E3) |
| A6 cross-lingual | direct voyage-4 vs translate-query | cross-lingual 20; recall@10 | +5 pp and p<0.05 | extra Haiku call = latency |
| A7 citation grain | paragraph vs sentence spans | all cited answers; span-support (deterministic) | +5 pp support or equivalence within +/-3 pp (TOST) at lower latency | ev §E5 [PREPRINT] |
| A8 injection | datamark arm; scanner arms (Prompt Guard 2, InjecGuard-class) | injection sets + slice G; ASR | ASR drop >= 5 pp absolute AND <= 1 pp loss in verified-citation rate and numeric-gate pass; scanner arm only if FPR <= 1% on real chunks | licence and CPU latency |
| A9 reranker | rerank-3-lite vs rerank-2.5-lite (now "older", ev §0.11) | all 200; recall@10 | non-inferior (TOST +/-3 pp) then pick the current model | same price |

Rule when a slice has n < 30: the arm needs the exact test to pass, or it stays flagged OFF and the slice grows (weekly added items). A +5 pp point gain with p >= 0.05 is "inconclusive, not adopted" (the safe default of D-R4-3). Honest power: 200 paired items at ~10% discordance detect about 7-8 pp (ESTIMATE, ev §E7), so a true 5 pp gain is often undetectable; the protocol accepts that.

Release gates (blocking, weekly full run and before demo; proposed lines are the author's, not sourced): citation verified >= 0.95 and faithfulness >= 0.90 (existing, ADR-017); zero ungrounded numbers in released answers on the 200; zero cross-tenant/ACL/cross-cell leaks; unanswerable-correct-refusal >= 0.90; recall@10 non-inferior to the last release (paired lower bound >= -2 pp); numeric-gate false rejects on correct answers <= 3%; indirect-injection ASR <= 3 of 300 trials (upper 95% about 2.9%).

Guardrail eval sets (record licence at integration, ev §1.7): PII = ai4privacy openpii-1.5m (CC-BY-4.0 per card; 2,000 sampled en/de/fr) + Gretel finance multilingual (Apache-2.0; 2,000), per-class precision/recall; IBAN and account numbers have no class in openpii, so add generated cases with valid checksums; pass: measured recall >= 0.90 on must-redact classes or the ADR-009 "no recall guarantee" statement stays and Presidio stays in front of a stricter rule list. Direct injection = Lakera gandalf (MIT, 1,000), deepset (662; licence conflict: smoke only), JBB benign (over-refusal) + the golden questions as benign; pass: recall >= 85% at FPR <= 2% on benign advisor questions. Indirect = LLMail-Inject (MIT) strings wrapped into 300 real chunks + 300 clean real chunks per source; pass: scanner FPR <= 1% on all real chunks (about 250 quarantines is the review budget), end-to-end ASR above. Not covered: toxic/off-topic sets (gap, ev §1.7).

Stats method (paired, document-clustered): binary metrics by exact McNemar on discordant pairs; continuous metrics by aggregating per document first, then a sign-flip permutation test over documents (avoids pseudo-replication); paired bootstrap over documents reported as descriptive only because evalstats advises against bootstrap CIs at N < 100 and our effective N is ~90-110 (ev §1.6 tension flagged by the skeptic); Holm across arms; TOST margins +/-3 pp for "no regression"; report n, n_eff and SE per slice; slices < 30 labelled directional.

Evidence: ev §1.5-1.7, §E1-E7. Rejected: FinanceBench/FinDER/FinTextQA (NC, ev §1.5), ObliQA as gate (UAE law; smoke only), full LLM-judge gates without calibration. Cost: baseline run 200 items x ~8k input + 0.5k output tokens = 1.6M in x $2 + 0.1M out x $10 = $4.2; weekly x4 = $17/month; nine arms once = about $40 one-off; Haiku judge < $1. Cap with `EVAL_BUDGET_USD`. Strongest dissent: 200 items cannot statistically separate most arms; counter: K-R4-4 chose it, retrieval-level deterministic metrics have more power than judged ones, and "inconclusive means off" prevents unmeasured methods from entering.

## 13. Edge-case catalogue (task 10; brief C.3 first ten, then added)

Gate tiers: PR = compose, every pull request (budget < 12 min); N = nightly on main; W = weekly (uses providers or real sources, or cloud).

| # | Scenario | Design control | Proving test | Tier |
|---|---|---|---|---|
| 1 | Delete during ingest | advisory lock + tombstone-first + indexer re-check in tx + silver post-write check (R4) | race harness: N interleavings of erase vs indexer; end state has zero rows/objects | PR |
| 2 | ACL change during a streaming chat | entitlement_version re-read per retrieval step and before `done`; abort `ENTITLEMENT_CHANGED` | slow fake LLM, change ACL at token 20, assert abort, message `refused`, no citations released | PR |
| 3 | PUBLIC doc updated while cached | version publish bumps corpus_version + purges cache by `source_document_ids`; key has as_of and source_epoch; hit-time verifier | cache a cited answer, publish new version, same question: miss and new text; race variant: hit inside the publish tx re-verified | PR |
| 4 | Duplicate document in two firms (and firm + PUBLIC) | per-tenant bronze/chunks (no cross-tenant dedupe); exact-hash dedupe at fusion prefers PUBLIC | erase from firm A: firm B still answers, A's cache/BQ purged, B's untouched; counts per tenant | PR |
| 5 | Poison document | scan + contract gates, quarantine, batch circuit breaker, DLQ for parse crash | corpus of malformed HTML/PDF, zip-bomb-like size, injection payloads: none indexed, all in quarantine/DLQ, consumers continue | PR |
| 6 | Partial region outage | cell isolation; 421 not fallback; no cross-cell failover (stated) | compose: stop cell-eu: US passes, EU tenants get 503 with clear code, no US data touched | N |
| 7 | Kafka outage during deletes | Postgres steps + ledger + outbox are durable; `erasure_oldest_pending_age_s` pages > 4 h | stop Kafka, issue erasure: Postgres done, others pending; restart: all done, receipt phase 1 issued once (idempotent) | PR |
| 8 | Replay after bug fix | idempotent keys, tombstone-aware sinks, atomic publish | replay fixture corpus twice after a parser bump: hash equals single run, zero resurrection | PR |
| 9 | Clock skew on as_of | `as_of` from DB date; half-open ranges; system time only `clock_timestamp()` | boundary days (valid_from, valid_to, day before/after), app clock +/-2 h and DST day, same chunks returned | PR |
| 10 | Model retirement during a demo | readiness model probe, `demo-up` preflight 1-token call per pinned model, fallback model tested weekly | fake provider returns 404 mid-stream: SSE `LLM_UNAVAILABLE`, breaker opens, fallback path when flag on; deprecation date check | PR / W |
| 11 | Late or back-dated upstream version | order by source version key; range slotted under lock; sys_range records when learnt | feed `v3, v1, v2` in all permutations: identical final valid-time line | PR |
| 12 | Upstream withdraws many items (glitch) | two-listing rule + mass-delete breaker | listing returns 0 or drops 30%: nothing applied, connector frozen, page | PR |
| 13 | Silent edit, same version key new bytes | `silent_edit` event + new sys_range row | mutate fixture bytes: new row, alert, old row closed, as-of reproducible with `known_at` | PR |
| 14 | Restore resurrects erased data | ledger replay before traffic | restore a backup taken before an erasure into scratch: replay: counts 0 | W (cloud) / N (compose) |
| 15 | FCA revocation | `purge_source`, source class `erase` | run purge on fixtures: all stores empty for the source, receipt, cache purged | N, drill quarterly |
| 16 | Misrouted token (wrong cell) | cell-side `home_cell` check, no rows of foreign tenants | wrong-cell request: 421, DB query log empty | PR |
| 17 | Advisor in two firms | token per firm, tenant claim vs URL vs cell map | token A on firm B resource: 403/421; two sessions in one browser context keep separate currentUser | PR |
| 18 | Tenant move fails mid-copy | copy-verify-cutover, rollback | kill target mid-copy: source intact and unfrozen, target empty; success path counts + hashes equal | N |
| 19 | Embedding generation mixing | `embed_model` literal per tenant, query model asserted | green half-built: queries still blue; flip: green; wrong-model query raises | PR |
| 20 | Erase mid re-embed | delete by doc_id across generations | start backfill, erase a doc: zero rows in both generations, receipt | N |
| 21 | Injection in a real chunk | scan, JSON + nonce, tool allow-list, numeric and citation gates | slice G + LLMail wrapped chunks: ASR line of section 12 | W |
| 22 | Licence footer missing | `licence_footer` block | matrix over licence classes: each cited class yields required text; removing it blocks | PR |
| 23 | BigQuery DML on streaming buffer | batch DML after 30 min | erase a subject within 5 min of events: rows removed on next batch, none left | N |
| 24 | Langfuse delete not honoured | retry + alert at 24 h | stub returns 202 without deleting: alert fires, receipt stays phase 1 | PR |
| 25 | UK source asked as of a date we never had | `valid_from_basis='observed'`, refuse pre-observation as-of | FCA question as of 2019: refusal "no version history for this source" | PR |

PR-gate additions to L0 (existing leak matrix stays): contracts, race harness, as-of boundaries, numeric-gate property tests (hypothesis over locale formats), footer matrix, role x tool matrix, replay idempotence, reconcile on fixtures, cell isolation. Connectors run against recorded fixtures (VCR) in PR; live source smoke, golden-200, guardrail sets, ablation arms, cloud canary and the restore drill are weekly.

## 14. Impact on epics (published: 6 epics, 103 tickets; E0-E3 done, E4 to T17)

| Epic | Verdict | Change |
|---|---|---|
| E0 Foundation | update | `docker-compose.cells.yml`, VCR fixtures, race-harness helpers, compose profile for Kafka-kill; image pinned to Cloud SQL version |
| E1 Identity and tenancy | update | `tenants.cell_id`, `residency_class`, `pseudonym_id`, 421 check, per-firm IdP tenants, 5-minute same-email test first; demo multi-tenant stays |
| E2 Gateway and edge | update (small) | per-cell hostnames, `resolve` route serving `cells.json`; Kong unchanged |
| E3 Retrieval v2 | update | `as_of` predicate, valid_range, chunk range merge reads, partial-index spike with 30% superseded rows, embed_model literal; done tickets stay (migration adds columns) |
| E4 Agent and guardrails | update | numeric gate, licence footer, as-of validity check, role policy table, entitlement re-check mid-turn, datamark arm flag; E4 tickets to T17 stay |
| E5 Kafka platform | update | `erasure.requested.v1`, delete-policy retention config, tombstone-aware sink helper |
| E6 ETL | update | pipeline gets atomic version publish, quarantine, `source_observations`; real connectors move to new E11 |
| E7 Evaluation | update (large) | 200-item golden set, private slice, tiers, nine arms, guardrail sets, stats protocol, release gates, budget cap |
| E8 Frontend | update (small) | firm switcher, as-of chip, jurisdiction chips, licence footers, quarantine view for compliance role |
| E9 Observability | update | reconcile, erasure and guardrail metrics, window dashboards |
| E10 Cloud deploy | update | backup retention 7 d, soft delete 0, `max_time_travel_hours` 48, log retention 7 d, KMS KEKs, restore drill, cloud canary, costed second-region ADR |
| E11 Real data onboarding and versioning (new) | new | connectors, change capture, bitemporal schema, version publish, contracts, quality, FCA kill switch |
| E12 Data lifecycle: deletion, proof, reconciliation, re-embedding (new) | new | erasure worker and ledger, receipts, canary, reconcile, embed generations, backfill/replay |
| E13 Regional cells and multi-login (new) | new | signed directory, cell isolation, two-cell compose tests, move-tenant, multi-firm login |
Order: E11 after E6 and E3; E12 after E11 and E5; E13 parallel with E11, its move-tenant ticket after E12; E7's real golden set starts as soon as E11 delivers the first corpus.

## 15. New ADR titles (026+)

026 Source connector framework, listing-diff change capture and source classes (retire vs erase). 027 Bitemporal documents and chunks on Postgres 16 ranges, as-of semantics and cache key. 028 Atomic version publish, tombstones and per-document locking. 029 Erasure architecture: store windows, unlinking, ledger replay, no per-subject KMS. 030 Proof of deletion: receipts, canary drill and the tombstone invariant. 031 Regional cells with a signed static directory and per-cell PUBLIC ingest. 032 Multiple logins: one Identity Platform tenant per firm, no cross-firm identity merge. 033 Tenant move protocol (copy, verify, cutover, erase). 034 Data contracts, quarantine and reconciliation. 035 Embedding generations (blue/green). 036 Guardrails on real data: ingest scan, numeric gate, licence footers, role policy. 037 Real golden set, guardrail sets, ablation protocol and statistics. 038 Residency promise wording and the LLM egress rule. Amendments: ADR-009 (scan + gates), ADR-014 (versioned silver path), ADR-015 (cache key), ADR-016 (arm, not default), ADR-017 (200 set, tiers), ADR-022 (lock with ingest), ADR-013 (topic retention).

## 16. Failure modes of the new design (10x load, dependency down, bad input)

- 10x load: new work is offline (ingest, reconcile, erasure). Chat path adds one equality predicate, one entitlement read per tool step, two regex gates. Voyage backfill is capped at 25% of RPM so 10x ingest cannot starve queries. Erasure batches are rate-limited by BigQuery's 2 concurrent + 20 queued DML per table: one batched DELETE per hour, so 10x subjects still means one statement.
- Dependency down: Kafka down = outbox grows, erasure Postgres steps still run (R5); BigQuery down = steps pending, receipt phase 1 only; Langfuse down = retry, alert at 24 h; Model Armor down at ingest = quarantine (fail closed); at query = existing fail closed; FCA/EUR-Lex/eCFR down = connector retries with backoff, no deletes inferred (zero-item listing is a failure); `cells.json` unreadable = last good copy plus baked fallback; Identity Platform down = existing cached keys.
- Bad input: malformed source returns 200 with HTML error page => contract fails, quarantined; listing shrinks => breaker; license field missing => cannot index.
- Residual unmeasured: PITR retention days, Kafka `segment.ms` editability, HNSW build time, Model Armor latency, Presidio recall, KMS token cost of destroy bursts: each has an owner test above.

## 17. Cost summary (monthly delta over the current plan)

Embedding $0 (free tokens), Model Armor < $1, KMS $0.18, backups/logs ~$1, restore drill ~$1-2, GCS/BigQuery storage < $1, weekly golden-200 run $17, ablation arms $40 one-off (about $7/month over 6 months), judge < $1, cloud canary ~$0.1, second cell $0 (not deployed). Steady delta about $22-30/month; first two months about $45. Inside $100-200 if the current plan leaves headroom (current spend not given: ASSUMPTION). Local RAM for two-cell compose is the real cost (4-6 GB, ASSUMPTION).

## 18. Main risks

1. FCA API: licence texts conflict, API format and rate limit unseen (ev §1.3); mitigated by kill switch, but a revocation mid-demo removes UK COBS. Ask FCA for written consent in parallel.
2. Publisher documents (KID, 497K, ADV): no licence, legal view pending (ev §0.3); mitigated by private-only, quote cap, no public eval, but the footer rules assume counsel agrees.
3. Erasure windows: Kafka `segment.ms`, PITR days and Langfuse dataset-copy behaviour are unverified; SLA numbers stay draft until canaries measure them.
4. Residency promise: no EU/UK LLM path (ev §0.4); if Keshav wants an EU claim, retrieval must exclude private EU documents or Claude on Vertex EU must be tested.
5. Statistical power: 200 items and ~110 effective cannot separate small effects; "inconclusive = off" means several methods may simply not enter.
6. Complexity: ~13 new tables/jobs for a demo; the controls are cheap but the test matrix (25 cases) is real work; E11-E13 sizing must be honest.
7. Same-email-two-tenants untested in Identity Platform (ev §3.2); if it fails, multi-login UX degrades to aliases.
8. pgvector filtering with superseded rows and RLS is an evidence gap (ev §2.2): recall could drop; the partial-index trigger exists.
9. Guardrail latency and accuracy (Model Armor, Presidio) are not found in vendor docs: budgets in section 11 are estimates until measured.

## 19. What this makes harder later

Every new store or event topic must register an erasure step and a reconcile pair (a new lint: a table or topic without them fails CI). Parser changes become planned re-baselines. Moving off Postgres ranges to PG18 temporal constraints later is a migration, not a flag. Adding a real second cell means operating two Confluent clusters, two Langfuse accounts and two BigQuery locations; the design makes that mechanical but not free. Per-subject cryptographic erasure is deferred; if a customer demands it, the per-subject DEK lives in a new table and KMS quota (100 write TPM) becomes the constraint.

## 20. Questions for Keshav (only what evidence cannot answer)

1. Ask FCA for written consent now, or keep API-only plus kill switch (K-R4-2 says API-only)? 2. Counsel view on publisher documents and the footer wording. 3. Accept the draft erasure SLA wording (24 h live, 14 d analytics and streams, 7 d backups) or prefer "no subject rows in BigQuery" to cut it to 24 h? 4. Run the Identity Platform same-email test. 5. Accept "model calls are US/global; EU-only private documents are excluded from retrieval in a cell without an EU LLM path" as the residency promise.
