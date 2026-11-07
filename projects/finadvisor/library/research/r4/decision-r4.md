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
