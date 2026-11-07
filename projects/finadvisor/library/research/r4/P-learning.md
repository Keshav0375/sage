OPTIONS

# P-learning: round 4 stage 2 design, lens LEARNING VALUE WITHIN BUDGET

Written 2026-11-02. Scope: changed parts only. Evidence = evidence-r4.md (cited as `ev §n`, tags kept: CORRECTED, UNVERIFIED, UNSUPPORTED, [PREPRINT]). Binding: K-R4-1..4, overview §1.2 (Kong, FastAPI, React/TS, demo multi-tenant in E1, $100-200/month). Arch refs: ov = overview/NN, ADR-0NN.

## 0. Lens, thesis, assumptions

Lens: every choice must (a) show a skill a senior data/ML-platform reviewer recognises (bitemporal modelling, deletion with measured windows, cells, contracts + reconciliation, blue/green re-embed, guardrail and RAG evaluation with honest statistics), (b) cost < ~$20/month more than the $110-160 demo month (ov 02), (c) be one-person buildable. Where two designs teach the same thing, take the cheaper. Where the evidence does not support a claim, the design measures it and publishes the number instead of asserting it (this is itself the portfolio signal).

Thesis in one line: one metadata spine (source registry, lifecycle state, valid-time ranges, tombstones, receipts, reconciliation manifests) carries versioning, deletion, cells, replay and eval; no new infrastructure beyond Postgres 18, the existing GCS/Kafka/BigQuery/Dagster, one KMS key per cell.

Assumptions (flag if wrong):
- A1 Corpus after the first source set: 10-30 MB text, about 2.5-7.5M tokens, about 7k-21k child chunks (350 tokens), plus about 10x for versions of PRIIPs/eCFR only where versions are in scope: <= 40k chunks total. Basis: ev §1.4 (Pt 275 225 KB; 143 eCFR version records; 9 PRIIPs files ~0.5-1 MB; 497K ~5 MB; five EU acts x versions ~40 MB one language [estimate]).
- A2 Real people stay synthetic (D-R4-2). Erasure machinery is built and drilled on synthetic subjects; no real-data claim.
- A3 Baseline demo month $110-160 (ov 02 line 45). Headroom to $200 = $40-90.
- A4 TTFT targets: p50 2.0 s, p95 3.5 s (brief). Latency numbers for guardrails are ALLOCATIONS to be measured in E4, not measurements (ev §4: Model Armor, Presidio latency NOT FOUND).
- A5 Cloud SQL moves from PG16 (ov 05 says 16) to PG18: needed for temporal keys; Cloud SQL PG18 default 18.6 CONFIRMED (ev §2.2). E0-E3 are published as complete, so this is a re-open (risk R1).

## 1. Diagram (data flow, cells, deletion)

```
CONTROL PLANE (global, tiny, no tenant content)           DATA PLANE: one CELL per region (us cell deployed, eu cell compose-tested)
 +--------------------------+                              +------------------------------------------------------------------+
 | directory: tenant->cell, |  signed cells.json (GCS)     | Kong -> chat-api (as_of, policy.yaml, numeric gate)              |
 |  idp_tenant_id, status   |<---------------------------->|   |                                                              |
 | Identity Platform (global|  host routing eu./us.        |   v          reads                                           |
 |  identity, tenant silos) |                              | Cloud SQL PG18: documents(+valid_during), doc_validity (WITHOUT  |
 | person_directory (opt.)  |                              |  OVERLAPS), chunks(+embed_model, +valid_during), tombstones,     |
 +--------------------------+                              |  erasure_ledger/receipts, recon_results, answer_cache            |
                                                           |   ^ writes (fa_worker)                                           |
 sources -> connectors (Dagster, per-source watermark +    | fa-worker: silver -> SCAN/QUARANTINE -> contextualizer -> indexer|
  overlap + weekly full-listing diff) -> observation       |   ^ Kafka (cell-local, envelope.cell_id check)                   |
  ledger -> GCS bronze (source_id/sha256) -> ...           | GCS bronze/silver (prefix = erasure unit) | BigQuery (cell location)|
                                                           | Langfuse project per cell | Cloud Logging (no PII, 14 d)         |
                                                           +------------------------------------------------------------------+
 Deletion saga: request -> ledger+tombstone (txn) -> outbox ErasureRequested -> per-store reapers -> receipts -> verify -> window timers
 Reconciliation: manifest per hop (source|bronze|silver|chunks|embeddings|BQ) -> recon_results -> alerts; drift or tombstoned-but-present = P1
```

## 2. D1: real source set, connectors, mapping (Track 1)

Choice. First set = the ev §1.4 set minus ESMA (not in K-R4 list; wave 2) with K-R4-2/3 applied. Every document gets `source_id`, `doc_key` (stable logical id), `licence_class`, `attribution`, `language`, `visibility`, `jurisdiction`, `tier_required`.

| source_id | content | access | licence_class | visibility | jur/tier (tier is a synthetic overlay, not a source property) |
|---|---|---|---|---|---|
| ecfr | 17 CFR 275 (39 sections) + versions (143 records, 9 removed); Pt 270 optional | versioner JSON + XML, gzip header, <= 1 rps (rate UNVERIFIED) | us_gov (terms page UNVERIFIED) | public | US, T1 (275), T2 (270) |
| sec_rr | RR datasets 2026q2 (82 MB zip) loaded as structured facts only (table arm A3), not chunked | SEC quarterly zip, 10 rps cap, UA | us_gov | public | US, T1 |
| edgar_497k | 3 fund families x 10-15 497K (~5 MB) | per-CIK submissions JSON, <= 5 rps, declared UA | publisher_unknown | private_demo | US, T1 |
| adv_brochure | 10-20 ADV 2A brochures (8 MB/PDF probe) | monthly zip mapping + per-firm PDF | publisher_unknown | private_demo | US, T2 |
| cellar_priips | PRIIPs Reg 1286/2014 consolidated (3 versions) x EN/DE/FR, RTS 2017/653, 1 corrigendum; MiFID II EN+DE optional | CELLAR REST + SPARQL, throttle | cc_by_4.0, label "not authentic" | public | EU, T1 |
| legislation_uk | eur/2014/1286 "(revoked)", 3 of 12 point-in-time versions; 2017/653 | /update feed, point-in-time URLs, UA, <= 3 rps (limit 1,500/5 min CORRECTED reading) | ogl_3 (+ 2011/833 dual) | public | UK, T1 |
| fca_handbook_api | COBS 9A, 6 current text only | API account, per-user rate limit (number NOT FOUND) | fca_revocable (cl.13 revoke + delete all copies; licence conflict UNRESOLVED) | public-but-revocable, own source kill switch | UK, T1 |
| kid_pdf | 2-3 KIDs (iShares EN+DE, DWS DE) | per-ISIN PDF | publisher_unknown | private_demo | EU, T1 |

Mapping synthetic firms to real documents (3 firms + PUBLIC + eval tenant):
- PUBLIC: ecfr, cellar_priips, legislation_uk, fca (only once FCA consent/account terms are settled; ships dark behind `SOURCE_FCA_ENABLED`). Public-licence documents are written only by `fa_etl_public` (existing rule).
- Firm A Atlas (US advisors, one US+EU advisor): edgar_497k (3 families), adv_brochure, synthetic firm policies. Firm B Brandt (EU, DE/FR): kid_pdf (DE/FR), synthetic DE policies. Firm C Crown (UK+EU): kid_pdf, synthetic UK policies. The same KID in B and C is deliberate (duplicate-in-two-firms edge case; bronze key is per tenant so delete in B never touches C).
- private_demo documents live in the firm's tenant (a firm "product shelf"), never PUBLIC, never in the repo, never in published eval sets; fetched at runtime by a job from a manifest in private config (K-R4-3). Output carries attribution; ESMA disclaimer N/A until ESMA wave.

Rejected: FINRA (terms ban ML use, ev §1.1); EDGAR companyfacts for funds (404 CONFIRMED); EDGAR FTS (403); crawling FCA website (cl.35.3 CONTRADICTED the earlier plan); ESMA in wave 1 (disclaimer work, no K-R4 ask); EUR-Lex data dump (EU Login, no gain).
Evidence: ev §0 items 1-3, §1.1-1.4. Cost delta: ~$0 (GCS < 1 GB; fetch free). Dissent (simplicity lens): ship eCFR + CELLAR only and skip legislation.gov.uk and the FCA API; the legal surface of the FCA API (revocation, unresolved licence conflict) buys little. Counter: the revocation path is exactly the "withdrawal" test and Keshav chose it (K-R4-2); it ships behind a flag.

## 3. D2: change capture (Track 2)

Choice. One `Connector` interface, one `source_observations(source_id, external_id, version_key, content_hash, source_event_time, first_seen, last_seen, withdrawn_at)` ledger, and four rules for every source: (1) a watermark per source stored in the same Postgres txn that registers the bronze object (Drive Changes pattern, ev §2.1); (2) an overlap window re-reading the last N days (Airbnb/Airbyte lesson: cursors miss silent edits); (3) a periodic full-listing diff as the backstop for hard deletes; (4) processing is idempotent on `(source_id, external_id, version_key)`, so late or out-of-order arrivals insert a version in the middle of history and the resolver re-splits valid ranges in one txn.

| source | primary feed (watermark) | overlap | full-listing backstop | withdrawal signal | notes |
|---|---|---|---|---|---|
| ecfr | `titles.json up_to_date_as_of`, then diff versions on (identifier, amendment_date, issue_date) | 14 d | weekly: complete versions list for Pt 275 | `removed:true` = valid_to + lifecycle `withdrawn` | `substantive:false` = editorial: new version, but hash dedupe avoids re-embed |
| edgar_497k | per-CIK submissions (acceptanceDateTime) + daily index | 2 d | weekly Saturday full-index reconcile (the only place removals show, ev §2.1) | accession absent from reconcile = `withdrawn_suspect`, needs 2 consecutive misses | 10 rps cap, we run 5 |
| cellar | SPARQL `cdm:lastModificationDate` > wm for the 5 base acts | 1 d | weekly full CELEX family listing | in-force flag / end-of-validity / repeal properties | corrigenda are separate CELEX linked to base act; carry CELEX |
| legislation_uk | `/update` publication log filtered to 4 items | 7 d | weekly hasVersion list | title "(revoked)" => valid_to; reason/date not read (ev gap), so store as `revoked`, date UNKNOWN allowed | applied/unapplied lag 4-8 weeks (secondary): state `known_pending` |
| fca_handbook_api | none (current-only API, no feed) | n/a | nightly full pull of the 2 modules, hash diff | absent provision or API 403/revocation = source kill switch | UK valid time before first sight is unknowable: `valid_from_known=false`, as-of answers say "as of first ingest" |
| kid_pdf / adv | per-ISIN/per-firm refetch weekly, ETag/hash | n/a | same | disappearing URL (404 twice) | KID states "accurate as at" date: parse into valid_from if present |

Late/out-of-order test fixtures come from real history: eCFR versions with amendment_date earlier than watermark, replayed in shuffled order; result must equal in-order result (property test: final `doc_validity` equal, chunk set equal).
Rejected: webhooks/RSS as primary (CELLAR RSS registration UNVERIFIED, none for eCFR/FCA); log-based CDC (sources are not databases); pure cursor without backstop (misses hard deletes, ev §2.1 Airbyte).
Evidence: ev §1.1-1.3, §2.1. Cost: $0 (Cloud Run job seconds). Dissent: a weekly backstop means a removed EDGAR filing can remain searchable up to 7 days; acceptable because eCFR/CELLAR/UK carry explicit signals and EDGAR filings are immutable by SEC (ev §1.1).

## 4. D3: bitemporal versioning on PG18 (Track 3)

Choice.
- One `documents` row = one version (already unique per `(tenant_id, bronze_sha256)`). Add: `doc_key`, `version_key`, `valid_during daterange`, `recorded_at` (system-from), `superseded_at` (system-to, null = current belief), `lifecycle` in (`pending_effect`,`current`,`superseded`,`revoked`,`withdrawn`,`quarantined`,`deleted`), `valid_from_known bool`.
- `doc_validity(tenant_id, doc_key, valid_during daterange, document_id, PRIMARY KEY (tenant_id, doc_key, valid_during WITHOUT OVERLAPS))` = current belief timeline; the PG18 constraint makes overlapping effect ranges impossible (btree_gist 1.8 present, ev §2.2). Empty ranges are not permitted: a version with valid_from = valid_to is rejected by the constraint (test).
- System time: `doc_validity_hist(... valid_during, sys_range tstzrange, reason, run_id)` append-only, with `EXCLUDE USING gist (tenant_id WITH =, doc_key WITH =, valid_during WITH &&, sys_range WITH &&)`: the classic bitemporal no-overlap. This exclusion form is textbook Postgres but NOT in ev; the E11 spike proves it on PG18.
- Queries: "as of V" = `doc_validity WHERE valid_during @> V`. "As known on S for V" (audit reproduction) = `hist WHERE valid_during @> V AND sys_range @> S`. Used for audit ("what did we tell the advisor on 3 March"), not on the chat hot path.
- No temporal FK anywhere (cannot CASCADE/RESTRICT/SET NULL, ev §2.2): `chunks -> documents` stay ordinary composite FKs; delete order is explicit in code (chunks, suitability_rules, doc_validity, documents).
- Chunk identity = `(doc_key, provision_path, valid range)` (legislation.gov.uk differs per section, ev §2.2). Chunks denormalise `valid_during` and `lifecycle` like the ACL columns. Supersession is a metadata UPDATE of the upper bound with zero embed calls (extends ADR-022; Notion two-hash trick: `chunk_hash` = text, `meta_hash` = ACL + validity, ev §2.1).
- Retrieval: SQL adds `valid_during @> $as_of AND lifecycle IN ('current','superseded','revoked')` and the existing iterative scan (filter after ANN; extra filter lowers selectivity, so `max_scan_tuples` is re-tuned in the E3 test). `as_of` is a date. Default = DB `current_date` in the firm's timezone, resolved once per turn at the database (single clock), stored in `messages.as_of`. Client `as_of` must be an ISO date <= today unless the advisor holds a "future-effect" flag (`pending_effect` documents).
- Answer cache key gains `as_of` (resolved date), `embed_model`, `source_policy_epoch`. A PUBLIC doc updated while cached: `corpus_version(PUBLIC)` bump already changes the key; a future-dated version taking effect at midnight changes `as_of`, so no bump is needed (this is the clock-skew trap); doc withdrawal/delete purges rows via the existing GIN on `source_document_ids`.
- `corpus_version` bumps once per ingest batch (not per document) or the cache flushes continuously.

Rejected: XTDB (non-destructive, conflicts with erasure; ev §2.2); SCD2 with `valid_to` columns and app-side overlap checks (no DB invariant; teaches less); plain range types without WITHOUT OVERLAPS (no PG18 value); full audit triggers on every table (cost). Evidence: ev §2.2 (PG18 DDL CONFIRMED, Cloud SQL PG18 CONFIRMED), §E2 (hard validity filter direction [PREPRINT]; magnitude not transferable). Cost: storage +~1 GB < $1/month; PG18 same price. Strongest dissent (simplicity): no one asked for system time; valid time + `recorded_at` is enough. Counter: the history table is ~40 lines and is the audit-reproduction story; keep it but never query it on the hot path.

## 5. D4: deletion everywhere (Track 4)

Three triggers, one engine: (a) source withdrawal/revocation (doc or whole `source_id`), (b) tenant admin delete (ADR-022 route), (c) subject erasure (synthetic advisor: conversations, messages, feedback, traces, analytics).

Engine: `erasure_requests(id, kind, scope, requested_at, verified_at)` + `tombstones(tenant_id, source_id, external_id, withdrawn_at, reason)` written in ONE txn with the status change `documents.lifecycle='deleted'` (the doc stops being retrievable at commit) and an outbox `ErasureRequested`; per-store reapers (idempotent, resumable) write `erasure_receipts(request_id, store, executed_at, verified_at, evidence_hash, window_ends_at)`. A request is `complete_live` when all live-store receipts verify, `complete_all` when the longest window has passed. Tombstones carry ids and a hash of the external id only (no content) and block re-ingestion and replay (resurrection test).

| store | mechanism | window (source) | proof |
|---|---|---|---|
| Postgres live | physical DELETE in order chunks, suitability_rules, doc_validity, documents; subject: messages/conversations/feedback/turn_events by advisor_id | minutes | re-query = 0 rows; `recon` negative check |
| Postgres backups | automated retention set to 7 d, PITR off in demo (log retention days NOT FOUND), no on-demand backups on the instance (they live "indefinitely"); no per-row purge exists (ev §2.3) | <= 7 d (our setting; ceiling = longest retention) | quarterly: restore into scratch instance after window, assert canary absent |
| chunks / HNSW | DELETE then partition-level `VACUUM`; dead index entries persist until vacuum (HNSW vacuum behaviour NOT in ev: spike) | minutes + vacuum | canary self-retrieval returns nothing; vectors are not plaintext (ev §2.3 BC inference) |
| answer_cache | DELETE via GIN on `source_document_ids`; TTL 24 h bound | seconds | row count 0 |
| GCS bronze/silver | object delete; bucket soft delete set to 0 on data buckets (default 7 d, cannot purge early, ev §2.3); layout `bronze/{tenant}/{source_id}/{sha256}`, `silver/tenant_id=/source_id=/doc=` so a source purge = prefix delete; no retention lock | immediate | list prefix = empty |
| BigQuery | analytics hold ids/hashes, no document text; subject rows removed by keyed-pseudonym unlinking (D5) + one nightly batched `DELETE` (2 concurrent + 20 queued DML limit) | 9-14 d for physical copies (time travel 2-7 d + fail-safe 7 d, ev §2.3); unlinked at once | count by pid = 0; time-travel query documented as residual |
| Kafka (Basic) | subject-bearing topics: retention.ms 7 d and segment.ms 1 d (retention max on Basic NOT FOUND: spike must set and read back); compacted state topics: tombstone, but max.compaction.lag.ms min 7 d (ev §2.3) | <= ~8 d estimate; compacted >= 7 d + cleaner | consume-from-start probe after window |
| Langfuse | DELETE trace/batch by `messages.trace_id`; sessions have no delete endpoint | ~15 min typical, not guaranteed (ev §2.3) | re-query; dataset items copied from traces: NOT stated, so never copy subject traces into datasets (eval datasets are built from the golden set only) |
| Cloud Logging | no PII by design (pseudonymous pid only); `_Default` retention 14 d (default 30); coarse `projects.logs.delete` exists (CORRECTED) | <= 14 d | exclusion-filter test + canary grep |
| Cloud KMS | scheduled destruction min 24 h | n/a for data; used for tenant KEK only | key state |

Honest SLA wording (publish as written, update only from drill output): "Erasure of live systems (database, search index, caches, object storage, traces) is executed within 24 hours of a verified request and proven by a per-system receipt. Copies we cannot purge on demand (database backups, BigQuery recovery windows, Kafka retention) expire on a fixed schedule; the last of them is gone no later than 15 days after the request, and the dated windows are measured each quarter with a canary subject and published. Model providers (Anthropic, Voyage) apply their own retention and are not covered by this statement." 15 d = BigQuery 14 d + 1 d. The 24 h figure is a target until the first drill measures it.

Proof of deletion: no prior design found (ev §2.3), so this is our design: receipts + negative reconciliation (every tombstoned key must have zero rows in every store, daily) + the quarterly canary drill: a synthetic subject with unique strings is written to every store, erased, then probed at 0 h, +24 h, +8 d, +15 d by Cloud Scheduler checks; measured windows go in `docs/erasure-windows.md`.
Delete during ingest: the indexer re-checks `documents.lifecycle <> 'deleted'` in its write txn (row lock), the reaper sweeps twice (second after `INFLIGHT_GRACE`, default 10 min); fault-injection test stalls the indexer after embed, issues delete, releases, asserts 0 chunks.
FCA revocation = (a) kind, scope `source_id=fca_handbook_api`: live stores minutes; backups <= 7 d (stated to FCA); bronze/silver prefix delete; derived data (chunks, embeddings) deleted too although cl.19 says Derived Data is ours (conservative).

Rejected: per-tenant/per-subject CMEK in Postgres (pool tenancy cannot; Cloud SQL standard backups/replicas after key destruction undocumented, ev §2.3); retention lock (irreversible, ev §2.3); soft-delete defaults left on (silently adds 7 d); Segment-style receipts copied from secondary sources (UNSUPPORTED). Evidence: ev §2.3 whole table, S2 hidden-assumption notes. Cost: ~$0 (jobs; backup storage < $1). Strongest dissent (reliability lens): 7-day backup retention with PITR off lowers recovery depth for a product with real data; for the demo it is the right trade and the ADR names the trigger (real data: longer retention + documented longer SLA). Second dissent: soft delete 0 removes accidental-delete recovery; bronze is re-fetchable from source (public) or runtime manifest (private).

## 6. D5: keyed-pseudonym unlinking ("crypto-shredding lite")

Choice. Outside Postgres, a subject appears only as `pid = HMAC-SHA256(subject_key, advisor_id)` (BigQuery, Kafka envelopes, Langfuse user id, logs). `subject_keys(tenant_id, advisor_id, wrapped_dek)` lives in Postgres, DEK wrapped by one tenant KEK in Cloud KMS (3-4 keys = ~$0.24/month; ev §2.3 price $0.06/key version/month; per-subject KMS keys rejected: 300 advisors = $18/month, 2,000 = $120/month, plus write quota 100 TPM from 2026-02-16). Shred = delete the `subject_keys` row; every external record becomes unlinkable at once, which removes the BigQuery 14-day and Kafka windows from the linkability question (the physical rows still age out). Residual: the DEK row sits in Postgres backups for <= 7 d, so the effective linkability window is 7 d, not 15 d; physical-copy window stays 15 d. Test: after shred, recompute pid is impossible; a retained BQ row cannot be joined to the advisor.
Embeddings are not decryptable plaintext and encrypting them defeats search (ev §2.3), so the live index relies on physical delete.
Rejected: Confluent field-level encryption (needs Stream Governance Advanced, price not read; "crypto-shredding" never named in docs); BigQuery AEAD shredding (no doc describes key destruction, ev §2.3). Strongest dissent: HMAC unlinking is pseudonymisation, whether it counts as erasure is a legal question; wording says "unlinkable", never "anonymised". Evidence: ev §2.3 (Spotify Padlock [OLD]: guarantee covers keychain deletion, not derived copies; same limit here). Cost: ~$0.3/month.

## 7. D6: regional cells, logins, moves (Track 5, K-R4-1)

Control plane (global, small, no content): `tenant_directory(slug, display_name, cell_id, idp_tenant_id, status, move_state)`, signed `cells.json` snapshot in GCS (readable if the home cell is down), Identity Platform (identity treated as global: data location unknown, ev §3.2), router config. Global fields disclosed in the privacy notice: firm slug and name, tenant-to-cell mapping, identity (email, uid). Everything else is per cell: Cloud SQL, GCS data bucket, BigQuery dataset in the cell location (cross-location JOINs error, ev §3.1), Kafka cluster (cell-local, no cluster links: link destinations need Dedicated/Enterprise, ev §3.1), Langfuse project (US Oregon or EU Ireland accounts are fully separate, ev §3.1), logs, KMS keys, Kong, workers.
Routing: host per cell (`eu.` / `us.`) through the existing ALB URL map (host rules, one serverless NEG per cell; default closest-region routing and no automatic failover, ev §3.1); SPA calls the directory on the global host, then talks only to the tenant's cell host. A request for tenant X on the wrong cell returns 421 plus the correct host; the cell never serves a foreign tenant (auth maps `firebase.tenant` through its own `tenants` table; unknown = 403). `envelope.cell_id` is checked at consume time (BC inference, ev §3.4): mismatch -> `dlq.v1`.
Multiple logins: an advisor in several firms has one Identity Platform user per firm tenant (silos, ev §3.2); the SPA keeps one auth instance per tenant (`currentUser` does not change on tenantId switch) and stores the active tenant slug (tenantId is not persisted). "Firm switcher" = switching which tenant's token is sent; there is never a merged principal across firms, so no cross-firm retrieval exists to leak. Token for tenant X presented to a cell that does not own X is rejected before any DB work. The same-email-in-two-tenants behaviour is UNVERIFIED: spike S1 (5 minutes) runs before E1 changes.
Moves (tenant to other cell; jurisdiction change of a firm): copy, verify, cut over, delete (Atlassian pattern [OLD], ev §3.4): (1) drain outbox, set `move_state=freezing` (chat 503 with a maintenance code for that tenant only); (2) export job as `fa_owner` with tenant predicate to the TARGET cell bucket (the only authorised cross-cell transfer, logged); (3) import, same embeddings (no re-embed), (4) reconciliation counts+hashes source vs target (D8), (5) directory flip, bump `corpus_version`, (6) source deleted through the deletion saga with receipts; on any failure delete target partial rows and unfreeze. Advisor jurisdiction change = `advisors` UPDATE (60 s principal TTL, cache key includes the jurisdiction set); mid-stream: the turn runs on its start snapshot and re-reads `entitlement_version`/`acl_version` before `done`; a downgrade aborts with `ENTITLEMENT_CHANGED` (tokens already sent cannot be recalled; exposure <= turn length).
Data that must not leave a region: all tenant content, vectors, conversations, traces, analytics, logs. Does leave: directory metadata, identity, and every prompt/chunk sent to Anthropic (inference_geo global or us only; us = 1.1x price, ev §0.4) and Voyage (regions UNVERIFIED). Claude on Vertex EU stays a costed option in the ADR, spike S2 tests availability; not built (K-R4-1).
Local two-cell compose test: `docker-compose.cells.yml` with two projects (cell_eu, cell_us), each: Postgres 18 + pgvector, Kafka KRaft, MinIO/fake GCS, BigQuery emulator or DuckDB file, Langfuse stub, chat-api + worker; plus control plane (directory, Kong with host routing, JWT-stub IdP emitting `firebase.tenant`); separate docker networks per cell plus a `probe` container proving eu services cannot reach us DB/Kafka (the compose analogue of IAM/VPC isolation). PR gate runs one Kafka with cell-prefixed topics (2 PG + app fits a 7 GB runner); weekly runs two brokers. Tests: wrong-cell 421; token-for-X-in-wrong-cell; event with wrong `cell_id` to DLQ; tenant move with verify-fail rollback; cell A outage leaves cell B green; directory snapshot serves while home cell down.
Cloud: one cell. A second real cell is a costed option (dominant driver Cloud SQL; every GCP unit price UNVERIFIED, ev §3.3); a 24 h "cell burst" drill (terraform apply, cross-cell tests, destroy) is the proposed stretch ticket, estimated <= $10 but to be priced with the calculator first.
Rejected: one global DB with a region column (fails K-R4-1 data-at-rest); Confluent cluster links (Dedicated/Enterprise ~$895/month); Spanner-style multi-region (budget); per-region Identity Platform projects (would split identity; cannot verify cross-region token checks, ev §3.2). Evidence: ev §3.1-3.4 (AWS cell article CONFIRMED: router thinnest layer, "start with a cell migration mechanism from day one"). Cost delta: $0 cloud (compose only); drill <= $10 one-off. Strongest dissent (simplicity): cells without a second deployed region is theatre. Counter: K-R4-1 chose it; the tests (wrong-cell, move, `cell_id` envelope) catch real design bugs, and the cell burst drill removes the theatre accusation for ~$10.

## 8. D7: data contracts, quality, lineage, reconciliation, backfill (Track 6)

Contracts (four layers): (1) source contract: Pydantic/Pandera schema per connector response, violation = `source_contract_violation` alert and the batch is parked (a source changing format must not poison bronze); (2) event contract: Pydantic -> JSON Schema in Schema Registry (ADR-013), compatibility BACKWARD within `.v1`, breaking = new `.v2` topic with dual consume, CI compares generated schema to registry; (3) silver contract: Pandera 0.35 on Parquet frames via polars (floor `polars>=1.20.0` CORRECTED; LazyFrame is schema-only unless `PANDERA_VALIDATION_DEPTH=SCHEMA_AND_DATA` or `collect()`; we set data depth explicitly and test it fails on a bad row); (4) gold contract: dbt `contract: enforced` on table models (views check names/types only), model versions with `deprecation_date` for breaking mart changes, dbt unit tests for SQL transforms (ev §2.2).
Quality gate: Dagster blocking asset checks between silver and index, PLUS the same rule enforced in the database (`documents.lifecycle` must be `indexable`, set by the check, and the indexer refuses otherwise) because cross-run semantics of blocking checks are not documented (ev §2.2, test before relying).
Lineage: queryable in the database first (`chunk -> document -> bronze_sha256, parser_version, chunker_version, embed_model, run_id`); OpenLineage via dagster-openlineage pinned at 0.2.1 as a learning emitter to a Marquez container in compose, never a gate (stale, 0.x, CORRECTED ev §2.2).
Reconciliation (daily Dagster assets, also after every backfill/replay/move): manifest = (count, order-independent multiset hash = sum of xxh64 over `chunk_hash` mod 2^64) per scope; hops:

| hop | expected | actual | tolerance |
|---|---|---|---|
| source -> bronze | `source_observations` live ids and content hashes | GCS listing and `documents` rows | 0 after pipeline lag p99 |
| bronze -> silver | documents indexable | Parquet doc files and row counts | 0 |
| silver -> chunks | per-document child count + set hash | `chunks` count + set hash | 0 |
| chunks -> embeddings | children with active `embed_model` | rows with non-null embedding | 0; plus canary self-retrieval top-1 |
| Postgres -> BigQuery | outbox/event ids per tenant per day | BQ `event_id` set hash per day | in-flight window only |
| tombstones -> all stores | zero rows | negative probe in every store | 0 always |
| ACL/validity drift | `documents` ACL/validity | `chunks` denormalised columns (meta_hash) | 0; auto-heal then alert |

Results to `recon_results` and BigQuery; log-based metric `recon_mismatch_total{hop,tenant}`; P1 = tombstoned-but-present, cross-tenant id seen, ACL drift (security); P2 = count drift beyond tolerance. Alerts are the symptoms; the table is the evidence. Prior art is thin (Airbnb framework [OLD, partial]; Notion hashes CONFIRMED), so the framework is ours and documented as such.
Backfill/replay: Dagster partitions (source x period/version), single-run backfills; replay from bronze, never from the source; envelope gets `replay_id`; consumers dedupe on `processed_events`; replay checks tombstones; atomic swap per document (new chunks inserted and superseded ones deleted in one txn); backfill concurrency bounded and Voyage token bucket capped at 25% of TPM so chat embed/rerank keep headroom (tier 1 only 2x at >= $100 billed, ev §2.5); `corpus_version` bumped per batch.
Rejected: Great Expectations (not covered by ev; Pandera + dbt tests already chosen); lineage as a hard gate; row-by-row comparison (cost). Cost: $0-2/month (BQ small queries inside 1 TiB free; jobs). Dissent (simplicity): reconciliation hop 5-7 is gold plating at 7k chunks. Counter: it is the data-engineering centrepiece for a reviewer, and the negative-probe hop doubles as deletion proof.

## 9. D8: re-embedding blue/green (Track 7)

Choice. The existing unique key `(tenant_id, chunk_hash, embed_model)` already allows two generations of one chunk text as two rows. So: `tenants.active_embed_model`, `tenants.building_embed_model`; `migrate` creates a partial HNSW per (tenant partition, model) `WHERE kind='child' AND embed_model='<m>'` with `CREATE INDEX CONCURRENTLY`; retrieval SQL filters `embed_model = $query_model`, where `$query_model` is the model that embedded the query, so a request that embedded before cutover simply reads the old generation (kept until grace), never a mismatched space. Steps: build (Dagster partitioned asset reads existing chunk text, no re-parse, batches <= request limits, dual-write for documents ingested meanwhile) -> verify gate -> per-tenant cutover (flip config, bump `corpus_version`, `embed_model` in cache key) -> retain old rows `REEMBED_RETAIN_DAYS=7` for rollback -> drop old rows and index.
Verify gate (all required): L1 recall@10 non-inferior to old by margin 2 points on the golden set (paired, cluster-aware) and on the 1,000-query screening set; canary self-retrieval 100%; row-count parity; ANN p95 within the §7.2 trigger (100 ms). Erasure during overlap deletes by document id across both models; backfill re-checks `lifecycle` per batch (hard delete mid-migration test).
Numbers (arithmetic on ev §2.5 prices/limits, tokens = chunks x 350): 100k chunks = 35M tokens: voyage-4 $2.10 (inside the 200M free tokens = $0), voyage-4-large $4.20; 1M chunks = 350M tokens: voyage-4 $21 ($9 after free 200M), large $42; wall time at base TPM: voyage-4 8M TPM = 44 min, large 3M TPM = 117 min, tokens/request caps 320K/120K so >= 1,100/2,900 requests (RPM 2,000 not binding). Batch (33% off, 12 h window) only above 1M chunks and loses the free tokens. HNSW build time/memory at 1M x 1024 halfvec is UNMEASURED: the scale drill builds on synthetic random vectors (no Voyage cost) and publishes the build time. Embed model retirement is covered like the LLM check (readiness fails on a retiring `embed_model`; Voyage deprecation policy not read: UNVERIFIED).
Rejected: in-place overwrite (no rollback, mixed space during build); separate index per model in a side table now (schema churn; trigger > 1M chunks); global (all-tenant) flip (loses per-tenant canary). Evidence: ev §2.4 (Notion generation-by-generation CONFIRMED; Tian Pan pattern is a single-author blog). Cost: one-off <= $1 at demo scale, scale drill $0 (synthetic). Dissent (simplicity): never re-embed in a demo; pure documentation. Counter: the architecture already pays for `embed_model` in the key, so the exercise is cheap and the A9 embedding ablation needs it anyway.

## 10. D9: guardrails on real data (Track 8)

Ingest-time scan and quarantine. Stage `scan` after silver parse, before chunks are indexable: (1) deterministic rules (imperative-to-assistant patterns, hidden/zero-width/bidi/tag characters, off-screen HTML, long base64) ~0 ms; (2) Model Armor document screening on extracted TEXT windows (document screening lists PDF/CSV/TXT/DOCX/PPTX/XLSX, not HTML/XML, so we send TXT; cap 4 MB and 65,536 tokens per window; `EXECUTION_SKIPPED` = not scanned = quarantine, fail closed; quota 1,200 QPM shared with chat; ev §4.1-4.2); a full 10 MB ingest = about 2.5M pricing tokens = $0.25 beyond the 2M free tier. (3) classifier arm (InjecGuard-class or Prompt Guard 2 22M; Llama 4 licence manually gated, ev §4.1) default OFF until it passes D-R4-3. Verdict stored on the document (`clean|suspect|quarantined`, detector, version, spans); quarantined = not indexable, visible only to `compliance_officer` role. Poison document (parser crash) = N=3 attempts then quarantine with reason, never an infinite retry.
Spotlighting. Default: retrieved chunks only inside a JSON-encoded `tool_result` with a per-request random boundary (Anthropic docs, ev §4.2). Datamarking is an ARM, not the default: the evidence tested GPT-3.5/4 in 2023 only, delimiting alone about halves ASR and authors do not recommend it, payloads without spaces bypass datamarking [PREPRINT, ev §4.2]; and the marker interleave would break the numeric regex and DE/FR number formats. If the arm runs, marking applies only to prompt rendering; the verifier runs on the unmarked stored text and strips the marker from model quotes first.
Numeric grounding gate (deterministic, per buffered sentence, same buffer as output PII redaction): normalise numbers, percentages, currencies, bps and dates across EN `1,234.56`, DE `1.234,56`, FR `1 234,56`, and date forms in three languages; every normalised value must occur in a cited chunk span or tool result or the user turn; rounding accepted only with "about/approx/rund/environ" and to the shown precision; unit conversion and derived arithmetic are NOT accepted (they fail, by design, until a calc tool exists). Modes `off|annotate|enforce`, default `annotate` ("figure not found in cited source" appended) until golden-set false-reject <= 3% of numeric claims, then `enforce`. Cost ~<= 10 ms/sentence (budget, to measure). Prior art: no paper for a plain gate; FiscalQA uses numeric tolerance scoring (ev §E5); FinGround rejected for hot path (8B detector, transfer 3-4 F1 worse [PREPRINT]).
Deterministic compliance checks (code, table-driven L0 tests): licence scope (`licence_class` -> required attribution footer: CC BY 4.0 + "indicate changes", OGL, "(c) FCA", EUR-Lex "consolidated text, not authentic"); `private_demo` documents never in exports or published eval; cited jurisdiction vs advisor primary jurisdiction (warning for multi-jurisdiction advisors; RLS still hides what they may not see); stale/superseded/revoked label from `valid_during` and `lifecycle` ("as of {date}, since amended/revoked on {date or unknown}"); existing suitability rules.
Per-role tool/output policy: `policy.yaml` (default deny, versioned, validated at boot, hash in traces): role x tool x output class. `as_of` is the only new tool argument (a date, validated). Quarantine evidence only for `compliance_officer`. `escalate_to_compliance` becomes two-step (tool creates a `pending_confirmation` proposal, the advisor confirms in the UI): the only side-effect tool cannot be triggered by injected document text alone (OWASP excessive agency). Strongest dissent (UX lens): extra click. Counter: it is the one control that holds even when every detector misses.
Metrics: per guardrail p50/p95 latency, timeouts, `EXECUTION_SKIPPED`, precision, recall, FPR, cost; Prometheus/Cloud Monitoring; weekly report table (D10).
Latency allocation, p50 / p95 targets (ALLOCATIONS, to be measured in E4; sum must stay < 2.0 / 3.5 s):

| step | p50 | p95 | note |
|---|---|---|---|
| auth + principal (cached) | 10 | 40 | |
| Presidio in-process | 40 | 100 | no vendor figure; must also cover DE/FR (see R5) |
| embed (Voyage) in parallel with Model Armor input (max of the two) | 200 | 600 | 500 ms timeout has no vendor basis (ev §4.2); measure |
| hybrid SQL (+as_of filter) | 80 | 150 | §7.2 ANN p95 trigger 100 ms |
| rerank | 150 | 350 | fall back to RRF |
| gate + cache lookup + verifier | 20 | 50 | |
| LLM TTFT (Sonnet 5.5 streaming) | 800 | 1,500 | |
| first-sentence buffer: PII redaction + numeric gate | 300 | 500 | buffer exists already; gate adds <= 10 ms |
| total | 1,600 | 3,290 | margin 400 / 210 ms: tight |

If the p95 margin is not met, the first lever is Model Armor to async-with-fail-closed-on-timeout only on the first turn of a conversation; the second is dropping rerank candidates.
Rejected: NeMo Guardrails (2057 ms CPU figure UNSUPPORTED but latency class is wrong for the hot path); LLM detectors on hot path (ADR-009); Qwen3Guard/Granite Guardian (GPU, harm focus); Anthropic Citations as primary (cannot combine with structured outputs; no precision figures). Evidence: ev §4.1-4.4. Cost: Model Armor <= $0.5/month; rest $0. Dissent (reliability): fail-closed Model Armor on the hot path makes chat depend on a service with no published SLA. Kept per ADR-009; metric + breaker; trigger to revisit = measured p95 or availability.

## 11. D10: advanced RAG and the real eval plan (Track 9, K-R4-4)

Golden set, 200 items, labelled by Keshav (39-56 h estimate, ev §1.6: unsourced). Composition (every item stores question, language, gold answer or "unanswerable", evidence span + `chunk_hash`, source `doc_key`/version, slice tags, split):

| slice | n | source mix |
|---|---|---|
| single-hop factual | 40 | eCFR 15, CELLAR 12, UK 8, 497K 5 |
| tables / numbers | 30 | RTS 653 annexes 8, KID costs 7, 497K fee tables 10, RR facts 5 |
| as-of / temporal | 25 | 10 state a date, 15 do not (default-date policy) |
| multi-doc / multi-hop | 30 | US vs EU, EN vs DE, base act vs RTS |
| cross-lingual | 30 | EN query -> DE/FR doc 15, DE/FR query -> EN doc 15 |
| unanswerable / out-of-jurisdiction / revoked-only | 15 | |
| conflicting or withdrawn source | 10 | eCFR removed, UK revoked |
| injection in document | 10 | planted into real chunks |
| compliance (licence label, stale, jurisdiction) | 10 | |

Splits: public-release subset (eCFR, CELLAR, legislation.gov.uk; about 140 items) is committable and feeds the CI gate; private subset (497K, KID, ADV, FCA; about 60) stays in the private bucket and runs only in the weekly Cloud Run `eval` job (K-R4-3; FCA text also kept private). Split by document cluster into dev (about 60, tuning) and test (about 140, final decisions) so arms are not tuned on the evidence that admits them.
Effective N (K-R4-4 asks > 100): require >= 70 distinct cluster ids (`doc_key`), <= 4 items per cluster; design effect = 1 + (m-1) x rho with m about 2.9: rho 0.3 gives 1.57 and n_eff about 127; rho 0.5 gives 1.95 and n_eff about 103. Every report prints measured rho and n_eff; if n_eff < 100 all comparisons are labelled directional. Slices < 30 are always directional (ev §1.6).
Screening set (cheap, synthetic, not a gate): about 1,000 retrieval queries auto-generated from real chunks (gold = source chunk; plus 300 as-of queries built from the 143 eCFR version records where the answer differs by version). Used only to prune arms before they spend the human set; biased toward lexical overlap, so never used to admit an arm.
External sanity: ObliQA Apache-2.0 retrieval smoke only (UAE data, ev §1.5). Public QA sets (FinQA, TAT-QA permissive; FinanceBench NC) are not used as gates (low fit).
Judge calibration: deterministic checks first (cited id exists, numeric-in-span, gold span retrieved, tombstone absent). LLM judge (Haiku 5.5, different from answerer) calibrated on 60 human-labelled answers: report kappa and rho^2; answer-level LLM-judged metrics count only if rho^2 >= 0.4 (below 0.2 unusable, evalstats [PREPRINT]) and kappa >= 0.6; otherwise they are directional.
Stats method: paired design, one outcome per item per arm. Headline test = sign-flip permutation on cluster-level paired differences (about 70 clusters), CI by test inversion, Holm across arms. Not item-level bootstrap (evalstats warns at N<100; clustered effective N is near that; the E7 research "paired bootstrap over clusters" is in tension, ev §1.6). McNemar exact reported as a secondary on discordant pairs for slices. "No difference" is never claimed: at 200 items, +/- 4-6 pp half-width (ev §1.6 table) cannot establish equivalence; the rule is "not shown, keep the simpler arm". Power honesty: at about 10% discordance a 7-8 pp swing is detectable (estimate, ev §E7), so a +5 pp gate is met only when the observed paired gain >= 5 pp AND the Holm-adjusted lower bound > 0; arms with true gains near 5 pp will often fail, and that is the intended conservatism.
Pass-line principle (D-R4-3, K-R4-4): quality methods enter only at observed gain >= 5 pp on their primary metric and target slice, lower bound > 0, no other slice worse by > 3 pp, latency/cost reported. Correctness and safety controls (validity filter, citation verifier, numeric gate, scan, policy) are required features measured by detection rate and false-reject rate, not by gain.

| arm | compared with | primary metric / slice | pass line | default if it fails |
|---|---|---|---|---|
| A1 context: free prefix (title+section path) / voyage-context-4 / Haiku contextual headers | B0 = ADR-008 with ADR-016 flag off | recall@10 on single-hop+tables | >= +5 pp; cheapest passing wins (CR costs 5.8-8.7x ingest tokens, Mangla [PREPRINT]; baseline 5.7% in Anthropic is dense-only, ev §E6) | flag OFF |
| A2 temporal validity filter | current-version-only | gold-version-in-top-5 and answer correct, as-of slice (25 + 300 screening) | reported; filter ON regardless (semantics); slice < 30 directional | n/a |
| A3 tables: header-repeating table chunks / deterministic RR lookup router / Docling | plain chunks | exact-match on 30 table items | >= +5 pp | plain chunks |
| A4 multi-doc: one-call Haiku decomposition + parallel retrieval | plain retrieval | answer correct, 30 multi items | >= +5 pp AND p50 TTFT delta <= +400 ms | off; no iterative loops (>= 2 hops cannot meet p50 2.0 s, ev §E3) |
| A5 cross-lingual: voyage-4 direct / query translation (Haiku) | direct | recall@10, 30 items | >= +5 pp for translation, TTFT delta reported | direct |
| A6 citations: paragraph vs sentence units | sentence | citation support (deterministic + judged), all | >= +5 pp (granularity [PREPRINT] shows model-chosen units, ev §E5) | paragraph |
| A7 injection: JSON-encode only / +datamark / +ingest classifier | JSON-encode | ASR on planted set (120 synthetic + 10 golden) | ASR down >= 5 pp AND clean-chunk FPR up <= 1 pp AND numeric-gate false-reject up <= 1 pp | JSON-encode only |
| A8 rerank: none / rerank-3-lite / rerank-2.5-lite (older, ev §0.11) | current pin | recall@10, nDCG@10 | pin the best of the two; keep rerank only if >= +5 pp vs none | none if it fails (saves the Voyage rate limit) |
| A9 embedding: voyage-4 / voyage-4-large / voyage-4-lite | voyage-4 | recall@10 | >= +5 pp for large (2x cost) | voyage-4 |
Guardrail eval sets and pass lines (pass lines are design choices, flagged): PII (Gretel finance multilingual Apache-2.0, ai4privacy openpii-1.5m CC-BY text; not 200k/300k/400k, ev §1.7): recall >= 0.85 per class in scope, reported per language EN/DE/FR; direct injection (deepset smoke only, Lakera gandalf MIT, JBB benign for over-refusal): over-refusal <= 2%; indirect: LLMail-Inject strings wrapped into 2,000 real clean chunks: recall >= 90% at FPR <= 1% (0 FP in 2,000 gives a 0.15% rule-of-three bound); numeric gate: >= 95% of 100 planted perturbations caught, false-reject <= 3% on gold answers; compliance checks: 100% on table-driven cases.
CI vs weekly: PR gate = deterministic guardrail suites, public-split 60-item retrieval + answer subset only when retrieval/prompt/policy paths change, all L0 edge tests marked `ci`; nightly/weekly = full 200 (private included), arms, guardrail sets, two-broker cell tests, reconciliation soak; quarterly = erasure drill windows, restore test, scale drill.
Eval cost (Sonnet 5.5 $2/$10, Haiku 5.5 $0.10/$0.50, ADR-006): answer-level run = 200 x (6k in + 0.6k out) = $2.4 + $1.2 = $3.6, judge about $0.1; weekly $4 = $16/month; PR subset 60 items = about $1.1, x 8 triggered runs = $9/month; ablation rounds 2 x 9 arms x $3.6 = about $65 one-off (retrieval-only arms are about free). Net monthly delta vs ov 02 baseline: +$10-20 (part of the baseline already includes evals).
Rejected: 300+ items (labelling 54-78 h, K-R4-4 chose 200); synthetic-only gold (the problem this round fixes); bootstrap CIs at N<100; LLM judge alone for citations (FinRegQA-EU: judges reward citation density [ABS]); agentic retrieval loops (budget). Dissent (rigour lens): permutation on ~70 clusters with a 5 pp bar will reject real gains; accept, log "not shown" with the interval, and use screening sets to explain.

## 12. D11: edge-case catalogue (brief C.3, all ten, plus extras)

Gate: CI = every PR (compose, L0); NIGHT = nightly or weekly job; Q = quarterly or on-demand drill.

| # | edge case | design control | test that proves it | gate |
|---|---|---|---|---|
| 1 | delete during ingest | lifecycle re-check in indexer txn, tombstone, double sweep | stall indexer after embed, delete, release: 0 chunks, 0 silver, receipt verified | CI |
| 2 | ACL/jurisdiction change during streaming chat | principal snapshot per turn; version re-read before `done`; abort `ENTITLEMENT_CHANGED`; cache key has versions | change tier mid-stream: stream aborts, no cached answer reused by the old tier | CI |
| 3 | PUBLIC doc updated while cached | `corpus_version(PUBLIC)` and `as_of` in key; cache hit re-runs verifier on fresh chunks | cache answer, ingest new version, same question returns miss; midnight validity boundary changes key | CI |
| 4 | duplicate doc in two firms | bronze key per tenant+source; unique per tenant | delete in B leaves C bronze/chunks/index intact; both retrievable by own firm only | CI |
| 5 | poison document | 3 attempts, quarantine, DLQ with reason, scan verdict | crafted parser-crashing and injection docs: pipeline continues, doc quarantined, other docs indexed | CI |
| 6 | partial region outage | cells isolated, directory snapshot, wrong-cell 421, no cross-cell fallback | stop cell_us compose project: cell_eu chat green, us tenants get 503 (not served by eu) | NIGHT (two-broker) |
| 7 | Kafka outage during deletes | delete is live in Postgres in the txn; reapers for GCS/BQ/Langfuse driven by receipts, retried from outbox; Kafka only informs | stop Kafka, delete doc: chat cannot retrieve it at once; restart Kafka: receipts complete, no reappearance | CI |
| 8 | replay after bug fix | replay from bronze, tombstone check, atomic swap per doc, unchanged text = zero embeds | replay a partition after a chunker fix: embed calls = changed chunks only; deleted docs not resurrected; recon green | CI |
| 9 | clock skew on as-of | single DB clock, date-typed `as_of` stored, future dates rejected | skew app clock +/-1 day across a validity boundary: same results as DB clock | CI |
| 10 | model retirement during a demo | readiness check for LLM and embed model ids, same-provider fallback gated by eval, `demo-up` preflight | mock retired id: `/readyz` fails; mid-demo 404 on model triggers breaker and fallback once, alert | CI |
| 11 | late/out-of-order source change | idempotent version key, range re-split | shuffled eCFR versions equal in-order result | CI |
| 12 | source withdrawal / FCA revocation | source kill switch + saga | revoke `fca_handbook_api` in compose: all stores empty by receipts; backups window printed | CI (fixture), Q (real windows) |
| 13 | tenant move with failure | copy-verify-cutover-delete, rollback | force hash mismatch: target cleaned, source unfrozen | NIGHT |
| 14 | advisor in two firms | per-tenant identity, per-tenant auth instance, no merged principal | two tabs, two firms: no cross-tenant read; token-for-X in cell for Y = 403 | CI |
| 15 | embedding cutover race | `embed_model = $query_model` in SQL, old rows retained | cutover mid-request: old-model query still answered from old generation; no mixed-space ranking | CI |
| 16 | poisoned retrieved text calls a side-effect tool | two-step escalation + policy.yaml | planted instruction in a real chunk: no committed escalation without UI confirm | CI |
| 17 | backup/provider windows | measured, not asserted | canary drill at 0 h/24 h/8 d/15 d; restore test after window | Q |
| 18 | source format change | source contract violation parks batch | mutate eCFR JSON field: alert, bronze untouched | CI |

## 13. Cost summary (monthly delta over the $110-160 baseline; one-offs listed apart)

| item | delta/month | one-off |
|---|---|---|
| PG18, versions, history tables, extra storage | < $1 | |
| GCS + silver/bronze (< 1 GB) | < $0.2 | |
| Model Armor ingest screening | <= $0.5 | |
| KMS (3-4 keys) | $0.24 | |
| Cloud Run jobs (connectors, recon, drills) | $1-3 | |
| BigQuery (recon, inside 1 TiB free) | ~$0 | |
| Eval additions (weekly 200 + PR subset) | +$10-20 | ablation rounds ~$65 |
| Re-embed at demo scale | ~$0 | <= $1; scale drill $0 (synthetic vectors) |
| Second real cell | $0 (compose) | optional 24 h drill <= $10 (UNVERIFIED price) |
| Total | about +$12-25 | about $65-80 |
Resulting demo month about $122-185: inside $100-200 but the top end leaves little room; the lever is running the weekly full eval only on demand (`demo-up`) and PR answer-level subset only on path-filtered PRs.

## 14. Operating burden

New standing chores: connector watchdog (source contract alerts), weekly recon review, quarterly erasure drill, FCA licence status, Cloud SQL minor-version lag (Cloud SQL pgvector 0.8.5 vs README 0.8.7, ev §2.2), model deprecation checks (existing), golden set upkeep (new regulation versions mean re-labelling affected items; track `doc_key@version` per item and flag items whose evidence version is superseded). Single-person load is realistic only because everything shares one ledger pattern (observation, lifecycle, receipt, manifest) and one scheduler (Dagster in Cloud Run jobs).

## 15. Impact on epics (existing E0-E10: keep / update / new)

| epic | verdict | change |
|---|---|---|
| E0 Foundation | update (small) | CI and compose images to PG18 + pgvector (tag existence to verify); re-run baseline Alembic and the RLS/pruning test on PG18; compose profile `cells` |
| E1 Identity and tenancy | update | `tenants.cell_id`, directory service and signed snapshot, per-tenant auth instances in SPA contract, 421 wrong-cell, spike S1 (same email two tenants), multi-login tests |
| E2 Gateway and edge | update (small) | host-based cell routing in ALB URL map and Kong config per cell |
| E3 Retrieval v2 | update | `as_of` filter, validity/lifecycle columns on chunks, `embed_model = $query_model`, partial HNSW per model, cache key additions, `max_scan_tuples` retune |
| E4 Agent and guardrails | update | numeric gate, policy.yaml, two-step escalation, ENTITLEMENT_CHANGED abort, licence/jurisdiction/stale labels, latency measurements; published tickets up to T17 need a keep/update/close pass |
| E5 Kafka platform | update | envelope `cell_id`, `replay_id`, retention/compaction settings, receipts topics, DLQ checks for cell mismatch |
| E6 ETL and data engineering | update (shrink) | connector work moves to E11; keep silver/scan/quarantine, atomic swap, per-batch `corpus_version`, source/prefix layout |
| E7 Evaluation | update (large) | 200-item golden set tooling and split, screening set, arms A1-A9, permutation stats, guardrail sets, CI vs weekly wiring |
| E8 Frontend | update | as-of picker, firm switcher, source/licence footer, quarantine review view for compliance officer, escalation confirm |
| E9 Observability and SLOs | update | recon metrics, erasure SLO and receipts dashboard, guardrail metrics, recon alerts |
| E10 Cloud deploy and operations | update | backup 7 d/PITR off, GCS soft delete 0, KMS keys, log retention 14 d, optional cell-burst terraform module, scale drill |
| E11 Real data onboarding and versioning (NEW) | new | source registry, connectors for 8 sources, observation ledger, bitemporal tables, mapping of firms, licence fields, tombstone-aware ingest, spikes (FCA account, CELLAR rate, exclusion constraint) |
| E12 Data lifecycle and deletion (NEW) | new | erasure saga, receipts, tombstones, subject pseudonym keys, per-store reapers, canary drill |
| E13 Regional cells (NEW) | new | two-cell compose, control plane, tenant move job, cross-cell probe, cell tests |
| E14 Data quality, reconciliation, re-embedding (NEW) | new | contracts, recon assets and alerts, backfill rules, blue/green re-embed, scale drill |
Dependencies: E11 -> (E5, E6); E12 -> E11, E5; E13 -> E1, E5 (parallel with E12); E14 -> E11, E3; E7 real-data tickets need E11. Waves: 1) S1/S2 spikes + PG18; 2) E11; 3) E12 and E14 in parallel; 4) E13; 5) E7 real eval.

## 16. New ADR titles (ADR-026+)

026 Source registry, licence classes and the first real source set (FCA revocable class, private_demo)
027 Change capture: watermark + overlap + full-listing diff + observation ledger
028 Bitemporal documents on PG18: valid-time WITHOUT OVERLAPS, system-time history, as-of retrieval and cache key
029 Deletion saga: tombstones, receipts, per-store windows, honest erasure SLA
030 Keyed-pseudonym unlinking for subject data outside Postgres
031 Regional cells: control plane vs data plane, host routing, residency scope and model-call carve-out
032 Multiple logins and tenant moves (copy, verify, cut over, delete)
033 Data contracts, reconciliation manifests and replay rules
034 Blue/green re-embedding by embed_model rows
035 Ingest-time injection scan, quarantine and spotlighting default
036 Numeric grounding gate, deterministic compliance checks, per-role policy, two-step escalation
037 Real evaluation plan: golden set, ablation arms, cluster-permutation statistics, pass lines
038 Postgres 18 upgrade (amends ADR-002, 003, 008 text and 05, E0 images)

## 17. Main risks

- R1 PG16 -> PG18 re-opens completed E0-E3 (migrations, pruning test under RLS + LIST partitions, pgvector iterative-scan behaviour under RLS/partitions NOT answered in ev). Mitigation: spike first, keep the PG16 path until the test passes.
- R2 FCA: licence conflict unresolved (OGL vs cl.3.3 vs Handbook licence agreement), revocation with "immediately delete all copies", backups hold text <= 7 d. Mitigation: dark flag, written consent request (open item), documented residual.
- R3 Publisher documents have no reuse licence: private demo only; a screen recording of the demo is itself a publication. Mitigation: attribution, visibility flag, no export, never in public eval.
- R4 200-item golden set may fail to show any 5 pp gain (power), and n_eff may fall under 100; Keshav's 40-56 h is an unsourced estimate. Mitigation: report "not shown" honestly, screening set, keep defaults simple.
- R5 Presidio spaCy `en_core_web_sm` is English only (ov 04); DE/FR names and EU documents are a recall hole. DE/FR spaCy models and Presidio multilingual config are not in ev: UNVERIFIED, E4 measures per-language recall first.
- R6 TTFT margin is thin (400/210 ms in the allocation) and every guardrail latency is unmeasured.
- R7 Kafka and BigQuery windows are documented limits, not measured; the 15-day wording depends on the first drill and on retention.ms being settable on Basic (UNVERIFIED).
- R8 Identity Platform behaviours (same email in two tenants, cross-region verification, data location) UNVERIFIED; the multi-login design assumes silos.
- R9 Scope: four new epics plus eight updates is a large re-plan for one person with AI builders; E13 and the optional cell burst are the first things to cut, E11/E12/E14 are the core.
- R10 Model calls leave the region (Anthropic global/us only): the EU cell's residency statement covers data at rest only, as K-R4-1 states.

## 18. What this design makes harder later

- Real firm data: needs longer backups, per-tenant keys (silo via `shard_id`), Confluent RBAC, self-hosted Langfuse, and a different SLA sentence; the pooled-tenancy deletion story gets weaker, not stronger.
- Corpus growth beyond 1M chunks: row-per-model re-embedding doubles table size during a build; move to a side table then.
- A second deployed region: Cloud SQL cost, Langfuse second account, Voyage region question and cross-cell analytics (BigQuery cross-location JOINs error) all become real work.
- Every new cache or index input must enter the cache key and the reconciliation manifest, or drift is silent.
- Golden-set maintenance: each regulation update can invalidate labelled evidence; the labelling cost recurs.
