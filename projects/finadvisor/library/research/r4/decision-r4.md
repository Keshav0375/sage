# finadvisor round 4: stage-2 decision (2026-11-02)

Decided by the orchestrator from three proposals (r4/P-simplicity.md, r4/P-reliability.md,
r4/P-learning.md), the skeptic check of the leader (r4/S-skeptic-3.md), the evidence
(evidence-r4.md) and Keshav's answers (checkpoint-r4.md, K-R4-1..4). Binding for stage 3.

## Base and rule of precedence
- Base design: **P-reliability.md** (sections R1-R11, edge-case catalogue §13, failure modes §16).
- This file overrides P-reliability wherever they differ. Items borrowed from the other proposals
  are named with their source.
- Status fact: tracker.json has 203 tickets, all `todo`. Nothing is built. "E0-E3 complete" in
  the brief means fully PUBLISHED. Changes to published tickets are `update` entries in the
  publish diff, not new tickets. (Corrects P-reliability §14 and S-skeptic-3 ordering notes.)

## Decisions

R4-D1 Sources and firm mapping: P-reliability R1 + K-R4-2/3. eCFR 17 CFR 275, SEC RR quarterly
  datasets (structured facts) + 497K, EUR-Lex CELLAR PRIIPs/MiFID EN/DE/FR, legislation.gov.uk,
  FCA Handbook API (current only). FINRA dropped. No Handbook crawling. Publisher documents
  (KIDs, 497K, ADV brochures) are `private_demo`: firm tenant only, never in the public repo or
  public eval sets. ESMA Q&As: optional, with the ESMA disclaimer on transformed text.

R4-D2 Change capture: P-reliability R2. One connector framework, append-only
  `source_observations`, full-listing diff is the truth for deletes, feeds only accelerate,
  two-strike withdrawal, mass-delete breaker. Source classes: law and Q&A are RETIRED (valid_to
  set, text kept for as-of); FCA API and publisher documents are ERASED.

R4-D3 Versioning on PG16 (M1 corrected): `daterange` valid time + `tstzrange` system time.
  - `document_versions` (unpartitioned): EXCLUDE USING gist on the parent.
  - `chunks` (LIST-partitioned per tenant, ADR-003): PG16 cannot declare EXCLUDE on a
    partitioned parent (S-skeptic-3 #1). The constraint goes into the per-tenant
    partition-creation migration, plus an L0 test that every leaf has it.
  - From P-simplicity: idempotent `reconcile_lineage()` for late, out-of-order, withdrawn and
    replayed versions; `valid_from` and `parser_version` are part of chunk identity, so replay
    after a parser fix re-parses (no "same bytes = no-op") and A-B-A reverted text is
    representable (S-skeptic-3 #5).
  - PG18 rejected: arch binds PG16, temporal FKs cannot cascade, PG18 re-tests E0-E3 assumptions.

R4-D4 As-of: P-reliability R3. as_of from the deterministic date parser, the UI chip, or the
  Postgres date in UTC; never from the model. The answer echoes the parsed as_of date. A
  post-generation check requires every cited chunk's valid_range to contain as_of. Answer cache
  key adds as_of, embed_model, source_epoch (amends ADR-015).

R4-D5 Atomic publish and locks: P-reliability R4 plus lock order (S-skeptic-3 #10): one document
  per transaction, advisory lock first, tenant `corpus_version` row last, for both publish and
  erasure.

R4-D6 Deletion (M2): physical delete on all live stores.
  - Queue: Postgres `deletion_requests` (from P-simplicity). No Kafka on the delete path.
  - Tombstone ledger keyed on (tenant_id, doc_key, sha256) with an explicit `release` action for
    legitimate re-ingest (S-skeptic-3 #3).
  - Write guards in every sink use UNCACHED point reads of the ledger (no 60 s cache), and
    erasure re-sweeps each store at the end of its window (S-skeptic-3 #2).
  - Subject rows carry a random `pseudonym_id`; deleting the mapping unlinks at once.
  - Ledger replay after any restore. Per-subject KMS keys rejected (cost per key, undocumented
    effect on backups; the quota objection was CORRECTED by the skeptic and is not a reason).
  - Store settings: GCS soft delete 0; BigQuery `max_time_travel_hours=48` enforced on every
    dataset including dbt-created ones; Cloud SQL backups 7 d; delete-policy topics retention 7 d
    with `segment.ms` set; logs 7 d and no PII in logs.

R4-D7 ACL changes off Kafka (S-skeptic-3 #4): acl-applier polls `acl_change_requests` in Postgres.
  Amends ADR-022. Kafka (ADR-013) keeps analytics and audit events only.

R4-D8 FCA revocation (S-skeptic-3 #6): FCA content lives only in the PUBLIC tenant and never
  enters Kafka or BigQuery (from P-simplicity). `purge_source('fca_api')` runs as the PUBLIC
  owner role, bumps source_epoch (cache invalidation), and fans out one erase job per firm tenant
  under that tenant's own role for messages and cached answers that quote FCA text. No
  cross-tenant role (keeps ADR-002 D13a).

R4-D9 Erasure promise (M3 corrected, S-skeptic-3 #7). Documented wording, not "instant":
  - Live stores (Postgres, index, answer cache, GCS): within 24 h of the system running. In
    demo-on-demand the erasure job runs first at every start.
  - Analytics and streams (BigQuery incl. 48 h time travel + 7 d fail-safe, Kafka): within 14 d.
  - Backups: within 7 d, plus ledger replay on restore.
  - Langfuse traces: provider best effort ("usually within 15 minutes"), stated as provider-bound.
  - BigQuery fail-safe and Cloud SQL PITR logs are documented windows, not observable; the
    canary measures only observable stores and runs at each demo start, not on a weekly cron.

R4-D10 Cells and residency (M4 corrected, S-skeptic-3 #9): P-reliability R7. Signed static
  `cells.json` directory, each cell holds only its tenants and returns 421 on mismatch, PUBLIC
  ingested independently per cell, tenant move = copy, verify, cutover, erase. Two-cell docker
  compose suite. Residency = data at rest (K-R4-1). Private EU text reaches Anthropic AND Voyage
  (embed and rerank); per-tenant `llm_egress_ack` flag must be true before private ingest.
  Cells do not isolate an LLM-provider outage; stated in the ADR. Real second region and Claude
  on Vertex EU: costed options only.

R4-D11 Multiple logins: P-reliability R7/ADR-032. One Identity Platform tenant per firm, one
  token per firm, no identity merge. The same-email-in-two-tenants test is a spike ticket that
  gates the Identity Platform tickets in E1 (E1 is not built).

R4-D12 Contracts, quality, reconciliation: P-reliability R8. dbt contracts + tests, Pandera at
  ingest, Dagster blocking checks, reconciliation counts + hashes at every hop with alerts.
  OpenLineage dropped (stale package). Hourly reconcile only while the system runs.

R4-D13 Re-embedding: P-reliability R9. Embedding generations as rows on
  (tenant_id, chunk_hash, embed_model), per-tenant flip, old generation kept for rollback, erased
  with the chunk. Times recomputed under the 25% rate cap (about 20 min at 100k, 200 min at 1M).

R4-D14 Guardrails: P-reliability R10. Ingest scan (Model Armor document screening + hidden-text
  strip) with quarantine; JSON-encode spotlighting by default, datamarking only as an ablation
  arm; locale-aware numeric grounding gate; deterministic compliance checks; licence footers;
  role policy deny by default; Presidio for EN, DE/FR PII recall measured before any claim.
  Model Armor latency measured from the Cloud Run region before the 500 ms timeout is fixed.

R4-D15 Eval and statistics (S-skeptic-3 #8): 200-item golden set (K-R4-4), public/private split.
  - Sampling: at least 40 source documents, at most 5 items per document.
  - Analysis at cluster (document) level; no fixed n_eff claim (ICC 0.3 had no source); the
    detectable effect is computed after a 30-item pilot and recorded.
  - At most 4 confirmatory ablation arms with Holm; other arms are exploratory and cannot enter
    the default pipeline alone (D-R4-3). Slices under 30 items use exact tests or stay
    exploratory.
  - Ablation runs use the Message Batches API (50% off).

R4-D16 Cost: Sonnet 5.5 at $2/$10 per MTok (official). Steady delta about $22-30/month; first two
  months about $45. A budget alert at $180/month guards the $200 ceiling.

R4-D17 Gap resolutions from the ADR writer (2026-11-02):
  - Confirmatory ablation arms (exactly 4, Holm): (1) LLM contextual retrieval vs the free
    section-path prefix (ADR-016); (2) voyage-context-4 contextualized chunks vs plain chunks;
    (3) rerank-3 vs rerank-2.5; (4) structured lookup (SEC RR facts, KID fee tables) vs table
    chunks. Exploratory only: datamarking, single-shot query decomposition, cross-lingual query
    translation, others. The temporal validity filter is a correctness control, not an arm.
  - `DELETE /v1/admin/documents/{id}` writes a `deletion_requests` row (ADR-029).
    `acl_change_requests` carries ACL and reclassification changes only (ADR-022 amended).
  - Cluster unit for the golden set is the PROVISION or PRODUCT, not the whole file: a CFR
    section, an EU article/annex, a COBS chapter section, a legislation.gov.uk provision, or one
    fund/KID/brochure. At least 40 clusters, at most 5 items per cluster. This keeps the floor
    reachable with the 8-12 public files of the first set.

## ADRs for stage 3
New: ADR-026..038 as titled in P-reliability §15, with R4-D3, D6-D11, D15 as above. Amendments:
ADR-009, 013, 014, 015, 016 (contextual retrieval = ablation arm, default OFF), 017, 022.

## Epics for stage 3 (plan.md)
E0-E10 updated where the decisions touch them. New: E11 Real data onboarding and versioning,
E12 Data lifecycle and deletion (incl. reconciliation), E13 Regional cells and multiple logins.

## Rejected, with the strongest dissent
- P-learning PG18 temporal keys: dissent "native WITHOUT OVERLAPS is cleaner and teaches more";
  rejected for the PG16 binding and no cascading temporal FKs.
- P-simplicity "live erasure within 15 min, all within 10 d": dissent "simpler promise"; rejected
  because nothing measures it and demo-on-demand stops the system.
- P-reliability "exclude private docs in a cell without an EU LLM path": dissent "real residency";
  rejected by K-R4-1.
- Crypto-shredding with per-subject KMS keys: dissent "provable delete in backups"; rejected for
  the undocumented backup effect and cost per key.

## Stage 3 validation decisions (2026-11-07)

Inputs: V-docs-db.md, V-docs-ai.md, V-consistency.md (this folder). Each item below gets an ADR
(new or an amendment block) through the arch-writer.

R4-D18 Validation verdicts:
  V1 Reranker: default `rerank-3-lite` (current, 4M TPM, 2000 RPM, $0.02/M, lower latency). Arm 3
     is rerank-3 vs rerank-3-lite: the full model enters only with a measured gain (D-R4-3).
     rerank-2.5 is "older" on Voyage's page and leaves the design. (V-docs-ai #2; fixes M2, M4.)
  V2 BigQuery: project default `default_max_time_travel_hours=48` (ALTER PROJECT), plus the
     per-dataset setting as a check; dbt does not set dataset options. (V-docs-db #2.)
  V3 Model Armor: behind a feature flag with a documented fallback (Presidio + heuristics,
     fail-closed for ingest quarantine, fail-open with an audit flag for prompts) because no GA,
     SLA or latency is published. (V-docs-ai #3.)
  V4 llm_egress_ack wording: Voyage zero-day retention only after an org-admin opt-out, which is
     irreversible; Voyage publishes no data region; Anthropic first-party is US/global.
     (V-docs-ai #5.)
  V5 Spikes: Cloud SQL backup expiry while the instance is stopped (E12); Identity Platform same
     email in two tenants (E1, gate). PITR log retention: Enterprise 1-7 d, set 7. (V-docs-db #3.)

R4-D19 Consistency must-fix decisions (V-consistency.md M1-M8):
  M1 Chunk identity is the 05-1 identity key (incl. valid_from and parser_version); embedding
     generations are unique on (that identity, embed_model). Fix ADR-035, 07, plan E6.
  M3 First-stage retrieval target: p95 ≤ 600 ms (embed then hybrid SQL is serial: 0.25 + 0.30 s
     estimated), measured in the E3 spike; TTFT targets 2.0 s p50 / 3.5 s p95 unchanged; recompute
     the latency budget in 02 and the E3 gate. Dissent: the MVP's 300 ms; rejected, the arch's own
     estimate cannot meet it.
  M5 chat.audit.v1 and eval.sample.v1 carry ids, chunk ids, hashes, scores and flags only, never
     answer or excerpt text. Text stays in Postgres messages (erasable). Fix 06 §6.4, ADR-013/023
     amendments.
  M6 FCA purge is a PULL model: purge_source writes a row to a PUBLIC `source_purges` table that
     every tenant may read; each firm tenant's erasure-worker run, under that tenant's own role,
     polls it and inserts its own deletion_requests. `fa_etl_public` gets no INSERT on firm
     tenants' tables; ADR-002 D13a stands.
  M7 05-1 §5.7: cache purge on document delete is done by the erasure-worker, not acl-applier.
  M8 Section pointers to the split deep-dive files: fixed by script (74 pointers, 44 files).
  Should-fix S1-S24 in V-consistency.md: apply all as written there, unless one conflicts with
  R4-D1..D19 (then follow the decision and note it).

R4-D20 Stage 4 ticket questions (2026-11-07):
  E11-Q1 REVISED: `source_purges` is created by E12-T6 (it depends only on E1); E11-T22 depends on it and writes the purge row in the same transaction as the source_epoch bump; E12-T19 reads it.
         erasure-worker only reads it. Arch table owner: E11.
  E11-Q2 as_of date parsing: ISO 8601 always accepted; numeric DD/MM vs MM/DD follows the advisor's
         jurisdiction (US month-first, EU/UK day-first); the parsed date is always echoed (R4-D4).
  E11-Q3 Operator release/reject/unfreeze: admin CLI only, no API endpoint in the demo.
  E11-Q4 `tenants.llm_egress_ack` column: added by E11-T14.
  E11-Q6 E3/E4 round-4 changes (cache key as_of/embed_model/source_epoch; as_of resolver) are
         folded into E3-T13 and E4-T18 by the stage-4 update writers.
  E11-Q7 ESMA connector (E11-T27) stays: its deleted Q&As are real delete test cases. Publisher
         document reuse is closed by K-R4-3 (private demo only).
  E13    cells.json signed with Ed25519 over RFC 8785 canonical JSON (CELLS_PUBLIC_KEY baked in);
         `tenant_moves` table in the source cell DB (E13); /resolve = Kong route to a chat-api
         endpoint backed by CellDirectory; privacy notice at docs/privacy-notice.md.
  E12    `erasure_ledger` (key tenant_id, doc_key, sha256; release action) is created by E12-T5
         with deletion_requests; a new E5 ticket provides the uncached sink-guard helper (depends
         on E12-T5); E5-T14, the E6 sinks and E12-T8 depend on it. `pseudonym_map` migration is an
         E1 ticket. E12 Terraform/KMS/export bucket land in E10, alert policies in E9. A canary store
         that does not reach zero inside its documented window is a FAILED canary: report store and
         age, raise the E9 alert, trigger an erasure-verify re-sweep.
  E0-E3  tenants columns cell_id, residency_class, source_epoch are added by E1-T4 (HOME_CELL
         default "us"; E13 sets real values); conversations and messages carry a random
         pseudonym_id (E1-T23); document_versions and chunk version FKs are E11-T4/T5;
         EMBED_MODEL_ALLOWLIST is owned by E3-T5 and reused by E12-T25; the as_of CI check covers
         SQL on chunks and document_versions.
  Arch touch-up (final pass): residency_class and pseudonym_id columns in 05 §5.2; config keys
         HOME_CELL, ERASURE_MAX_ATTEMPTS, EMBED_BLUE_KEEP_DAYS, MODEL_ARMOR_ENABLED in 06 §6.6;
         table owners per R4-D20 in 05.
  E4-E6  acl.changes.v1 stays as an analytics topic only (ADR-022 amended); the ACL path polls
         Postgres. Numeric gate: a failing sentence is withheld and the answer ends with
         ANSWER_WITHHELD + reason; earlier sentences stay released. calc tool arguments set in
         E4-T33; LLM_EGRESS_NOT_ACKNOWLEDGED refusal code (add to 06 §6.1). fa_etl_public and the
         sink roles get SELECT on erasure_ledger (E12-T5 grants; 05 §5.3).
  E7-E10 (answers to changes-E7-E10.md Q1-Q16):
   Q1  Quarantine summary: GET /v1/admin/quarantine/summary, compliance role, counts by source and
       reason code only (no text). Endpoint ticket E11-T28; UI ticket in E8.
   Q2  citation event carries per-citation `source_class` (public | firm | private_demo); GET
       /v1/conversations/{id} returns stored footers. E8-T15 labels per citation.
   Q3  Canary runs after demo-prewarm (still after the erasure job); a FAILED canary does not stop
       demo-up; the CRITICAL alert is the control.
   Q4  `erasure` job = one pass of the erasure-worker code as a Cloud Run job, role fa_worker.
   Q5  ledger-export: daily Cloud Scheduler row, fa_worker; erasure-replay: manual, run after any
       restore (no schedule), fa_worker.
   Q6  KMS_RECEIPT_KEY_ID and LEDGER_EXPORT_BUCKET are the names; erasure-verify reads Kafka with a
       dedicated read-only Confluent key (KAFKA_VERIFY_API_KEY/SECRET in Secret Manager).
   Q7  E10-T26 creates the GCS data bucket and fa_analytics dataset in Terraform (no E6 script).
   Q8  erasure-verify hourly at minute 30 while the system runs.
   Q9  Metric names follow the E11/E12 tickets; the 9.2 table adopts them and adds the missing rows.
   Q10 "page" = CRITICAL email alert, "ticket" = WARNING; a FAILED canary is CRITICAL.
   Q11 alpha 0.05/4 (Holm worst case), power 0.8, sign-flip simulation; labels are binary
       pass/fail; rho is the phi coefficient (Spearman on 0/1); gate rho^2 >= 0.4 (ADR-037).
   Q12 Keep the >= 25 synthetic probe cases outside the 200 (security gates, no cluster stats).
   Q13 EVAL_PRIVATE_BUCKET_URI and JUDGE_MIN_RHO2 go into 06 §6.6; the 30-item intra-rater relabel
       adds ~6-8 h to Keshav's labelling (total ~46-63 h).
   Q14 New tickets: E6-T22 voyage-context-4 chunk variant as an eval-only embedding generation
       (E12 generations); E4-T34 structured lookup tool over fund_rr_facts and KID fee tables
       behind a flag. E7-T7 depends on both.
   Q15 The SPA follows cell_hint only when its host matches the /resolve answer for the slug.
   Q16 Key order is cosmetic; dependencies decide build order.
