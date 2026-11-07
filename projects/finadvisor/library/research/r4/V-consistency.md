# r4 stage-3 validation: internal consistency audit (complete)

Scope: arch/ (architecture.md, architecture-diagram.md, deep-dive/*, decision-logs.md ADR-026..038 and the "Amended 2026-11-02" blocks) and epic/plan.md against decision-r4.md (R4-D1..D17) and checkpoint-r4.md (K-R4-1..4). Paths are under /Users/keshav/Projects/sage/projects/finadvisor/ unless absolute. No web research was needed.

Method notes
- Every relative link in architecture.md, architecture-diagram.md and deep-dive/README.md was resolved with a script: 0 missing files.
- Every ```mermaid block was parsed with mermaid 11.4.1 (`mermaid.parse` under jsdom): architecture-diagram.md, deep-dive 03, 04, 04-1 (6), 04-2 (2), 05, 07 (2) and plan.md graph all parse. Only deep-dive/00-as-built-baseline.md blocks 3 and 4 fail (see S18).
- Epic dependency graph in plan.md: 41 edges, no cycle; each epic's "Dependencies" line matches the graph (E10 "E2 through E9", E11-E13 list transitive epics in prose only). Every ADR-026..038 is owned by an epic (026 E11; 027 E3/E11; 028 E6/E11/E12; 029 E12; 030 E12; 031 E13; 032 E13; 033 E13/E4; 034 E11/E12; 035 E12; 036 E4/E11; 037 E7; 038 E11/E13). Edge cases #1-#10 each map to an epic exit criterion: #1 E12, #2 E4, #3 E3 + E11, #4 E12, #5 E11 (+E6), #6 E13, #7 E12, #8 E11/E12, #9 E3, #10 E4 (named in the E4 change list, not in its "Added to Done when" bullet, see S15).
- Checked and consistent with the decision (no finding): no Kafka on the delete or ACL path in any arch file (only superseded originals inside ADR-022/013, which carry amendment blocks); PG16 everywhere (PG18 appears only as the rejected option); contextual retrieval default OFF (ADR-016 amendment, 04 line 144, 06 key, plan E4/E6); no crypto-shredding (rejected in ADR-029, 01, 04-2, 11); erasure windows 24 h / 14 d / 7 d / Langfuse provider-bound identical in ADR-029, 02 §2.7, 04-2 §4.19, 05-1 §5.14, 11, architecture.md; uncached ledger reads in ADR-028, 04 §4.7, 04-2, 05-1, plan E5/E6; residency = data at rest in ADR-038, 08 §8.7, 04-2, architecture.md §3/§8 with the three egress paths and `llm_egress_ack`; cached tombstone reads absent; Sonnet 5.5 $2/$10 and the $180 alert consistent; ADR "Proved by" edge-case numbers (#1..#30) all exist in 07 §7.4 and match; error codes in 07/ADRs exist in 06 except TURN_EXPIRED and TENANT_NOT_FOUND (S11).

## MUST-FIX (8)

M1. chunk uniqueness contradicts the A-B-A / replay decision (R4-D3).
- decision-logs.md ADR-035 Context: "`chunks` is already unique on `(tenant_id, chunk_hash, embed_model)` (ADR-003)". deep-dive/07-scaling-failure-modes-and-recovery.md line 81: "chunks are unique on `(tenant_id, chunk_hash, embed_model)` and chunk identity includes `valid_from` and `parser_version`". epic/plan.md E6 line 234: "upserts (unique `(tenant_id, chunk_hash, embed_model)`)".
- vs deep-dive/05 `chunks` row and 05-1 §5.10/§5.5: identity (unique) is the 8-column key with `valid_from`, `parser_version`; the 3-column key "becomes a plain index".
- Fix: 3-column key is a non-unique reuse index in all three places. A unique 3-column key makes text A, B, A impossible (same chunk_hash twice), the property R4-D3 requires.

M2. Rerank model: three incompatible statements (R4-D17 arm 3, default model, unfolded verdict).
- R4-D17 / ADR-037 / 02 §2.10 / 11 line 40 / plan E3, E7: arm 3 = `rerank-3` vs `rerank-2.5`.
- vs default everywhere else: `rerank-2.5-lite` (ADR-008 line ~820, 04 lines 123 and 253, 04-1 Flow 1, 06 `RERANK_MODEL`, 02 §2.5, 11 line 40). The shipped default has no arm; the lite pair is never compared.
- vs arch/state.md "Validation verdicts not yet folded": "rerank-3 replaces rerank-2.5 as the default (ablation arm 3 = rerank-3 vs rerank-3-lite)", and r4/V-docs-ai.md: Voyage now lists rerank-3 as current, rerank-2.5 as "older".
- Fix: the orchestrator must pick once (decision R4-D17 says rerank-3 vs rerank-2.5; the docs check says otherwise), then edit ADR-008 (amend), 04 ×2, 04-1, 06, 11, 02, ADR-037, plan E3/E7 and state.md together. Whatever is chosen, the default model id and the two arm models must be the same tier (lite vs lite or full vs full).

M3. First-stage retrieval target is below the arch's own estimate (known item 3).
- architecture.md §2 line 10, 02 §2.1 table row "Retrieval first stage (embed + hybrid SQL) p95 < 300 ms", 09 line 54, plan E3 line 158 ("fail if above").
- vs 02 §2.1 budget: embed 0.25 s p95 + hybrid SQL 0.30 s p95 = 0.55 s serial (02 says so under "Reconciliation to do"). Embed only runs parallel to Model Armor, not to the SQL (the SQL needs the vector; 04-1 Flow 1).
- Fix: set first stage p95 target to about 0.6 s (the 3.5 s TTFT budget has 0.90 s p95 headroom) or lower the estimates to fit 300 ms and say they are targets; update architecture.md, 02, 09 and plan E3 together and delete the open note, because plan E3 turns it into a pass/fail gate.

M4. Rerank throughput: 2M vs 4M TPM (known item 3), and the 2M figure belongs to the wrong model.
- 02 §2.3 line 55, 07 line 20 and plan E3 line 156: "Voyage Tier 1: 2M TPM, about 5 QPS" for the default model; 02 and 10 item 7 add "E3 measures which applies".
- vs official table (07 line 142, 11 line 40, V-docs-ai.md, evidence-r4.md line 222): rerank-3 and rerank-2.5 = 2M TPM, rerank-3-lite and rerank-2.5-lite = 4M TPM, 2,000 RPM for all. The default is a lite model (4M, about 11 QPS at 6k tokens/query).
- Fix: one sentence in 02 §2.3, 07 row 20, 10 item 7, plan E3: capacity by model (2M full or 4M lite, 2,000 RPM, multiplied by Voyage tier); remove "which applies". Resolve together with M2.

M5. FCA text can reach Kafka and BigQuery through chat events (R4-D8, ADR-026: "FCA content never enters Kafka or BigQuery").
- decision-logs.md ADR-026, 03 line 54, 04 line 184, 06 line 62, 07 edge #15 test ("FCA content absent from Kafka and BigQuery"), plan E5 (a producer or sink check rejects the `fca_api` source on pipeline topics).
- vs 06 §6.4: `chat.audit.v1` carries "redacted text, retrieved chunk ids" and `eval.sample.v1` carries "redacted question, redacted answer, cited excerpts"; ADR-013 original "ids, hashes, redacted text only"; 04-1 Flow 1 writes these outbox rows after every turn. A UK answer quoting COBS text and its cited excerpt flow through Kafka to `chat_audit` / `eval_events` in BigQuery. No rule strips them, and the purge fan-out (04-2 §4.20) erases only Postgres messages and cache, "so those stores need no step".
- Also ADR-029 and 11 line 31 say subject-bearing topic payloads are "minimised to ids and `pseudonym_id`", which contradicts the text-bearing events above.
- Fix: add a rule (ADR-013 amendment, 06 §6.4, 04 §4.7): events for a turn whose cited chunks include `source_class = 'fca_api'` carry hashes and ids only (no question/answer/excerpt text), enforced by the outbox writer and tested in #15 against Kafka and BigQuery; or state that the redacted answers may quote FCA text and add erase steps for those two stores. The decision wording requires the first.

M6. Cross-tenant write grant contradicts "no cross-tenant role" (R4-D8, ADR-002 D13a).
- R4-D8 / ADR-026 / 08 line 72 / 04-2 §4.20 / 07 #15: "no cross-tenant role (ADR-002 D13a stands)"; ADR-002 D13a: "INSERT / UPDATE / DELETE = own tenant only; only `fa_etl_public` writes PUBLIC".
- vs deep-dive/05 §5.3 `fa_etl_public`: "INSERT on `deletion_requests` of firm tenants ... for the `purge_source` fan-out" and 05-1 §5.13: "`fa_etl_public` INSERT for firm tenants only". That is a write by a PUBLIC role into firm tenants' rows.
- Fix: either amend ADR-002 D13a with this one INSERT-only exception (and add it to the leak matrix), or use a pull model that keeps the claim true: `purge_source` writes one PUBLIC-tenant row/epoch bump; each firm's `erasure-worker` reads it (PUBLIC rows are readable by everyone) and enqueues its own `deletion_requests` row under its own tenant context. The decision text ("one erase job per firm tenant under that tenant's own role") fits the pull model.

M7. Stale: acl-applier purges the cache "on document delete" (R4-D17: deletes are `deletion_requests`, executed by the `erasure-worker`).
- deep-dive/05-1 §5.7 (line 86): "by the `acl-applier` on ACL change and document delete".
- vs 04 line 146, 04-2 §4.21, ADR-022 amendment, plan E4 line 200.
- Fix: "by the `acl-applier` on ACL change and by the `erasure-worker` on document delete".

M8. 61 section pointers in epic/plan.md and the published ticket files point at the pre-split files.
- plan.md (13 pointers) and epic/E*/epic.md plus ticket files (about 48), for example plan E11 "Arch sections: deep-dive/04-components-and-responsibilities.md#4.15 to #4.18, #4.25, 05-data-model-and-storage.md#5 (versioned documents and chunks), 06#6.4"; E12 "04-components...#4.19 to #4.23, #4.27, #4.17"; E13 "04-components...#4.24"; E7 and E10 "#4.14"; E3 "05-data-model...#5.5/#5.6/#5.7/#5.8".
- vs actual locations: 04-components holds only 4.1-4.13; 4.14 is in 04-1-key-flows.md; 4.15-4.27 are in 04-2-source-lifecycle-and-cells.md; 05-data-model holds 5.1-5.3; 5.4-5.14 are in 05-1-rls-indexes-versioning-and-deletion.md; connector and deletion contracts are 06 §6.7-6.9 (not §6.4).
- Fix: retarget these in the stage-4 publish diff; builders read by file and section.

## SHOULD-FIX (24)

S1. `rerank-2.5-lite` price: 02 §2.5 unit-price line says `$0.05/M`; 11 line 40 and evidence-r4.md say rerank-2.5-lite $0.02 (rerank-2.5 is $0.05).
S2. System-time column name: ADR-027 and 11 line 21 use `sys_range`; 05-1 §5.9 SQL, 04-2 §4.18, 05 use `system_range`. ADR-027's EXCLUDE predicate also lacks the `status NOT IN ('ingesting','quarantined','erased')` clause of 05-1. Use `system_range` and the 05-1 predicate everywhere.
S3. Cursor store: ADR-026 and 06 §6.7 line 196 say `source_state(source_id, cursor jsonb, overlap_s, last_listing_at)`; 04-2 §4.15 and 05-1 §5.9 put cursor/overlap/last_listing_at on `source_registry`; no `source_state` table exists in 05. Drop `source_state` from ADR-026 and 06.
S4. Wrong path to the decision file: ADR-038 line 7, plan.md line 5, state.md line 5 cite `library/research/decision-r4.md`; the file is `library/research/r4/decision-r4.md`. (ADR-025 cites `library/research/resolutions-r3.md`; not verified here.)
S5. 06 §6.6 `WORKER_ROLES` omits `erasure-worker`; 04 §4.7 line 139 lists it.
S6. Judge acceptance: ADR-025 R63 and plan E7 line 278 keep "Cohen's kappa >= 0.6" for judge calibration; ADR-017 amendment, ADR-037, 02 §2.10, 10 item 22 gate the judge on judge-human rho^2 >= 0.4. Mark R63 superseded and use one metric.
S7. K-R4-4 vs R4-D15/R4-D17: 01 §1.2 line 22 repeats "stays above 100 effective items after clustering by source document", while ADR-037, 02 §2.10 and plan E7 say "no fixed n_eff claim" and the cluster unit is provision or product. State in 02 §2.10 that the 100-effective-items criterion is replaced by the pilot-based detectable effect. Also 200 items with a floor of 40 clusters and a cap of 5 per cluster means every cluster must hold exactly 5 items (200/5 = 40); say so or raise the floor.
S8. Stale originals sit beside "Supersedes" lines: plan E4 line 180 and E5 line 210 ("acl_change_requests + outbox" for document delete; "ACL-column UPDATE or delete"), E3 scope bullet on the answer cache ("purge by the applier and `maintenance`"), plan.md "Planning notes" lines 429-431 ("ADR-022 says to be confirmed at planning"; "04#4.15 still mentions an erasure event"): ADR-022 is already definitive and no arch file mentions `erasure.requested.v1` (grep: 0 hits outside plan.md). Strike or tag the originals; delete the two stale planning notes.
S9. Edge-case count: plan.md line 5 says the catalogue is "r4/P-reliability.md section 13 (25 cases)" and "N / W" tiers; deep-dive/07 §7.4 has 33 cases and tiers PR / nightly / weekly or demo start. Update plan.md line 5.
S10. 06 §6.4 topic table: the column titled "Retention" contains "E5" in every row (an epic id), and no per-topic retention is given; the 7 d / `segment.ms` 1 d rule is only in prose. Rename the column "Owner epic" and add a Retention column naming which topics are subject-bearing (delete policy, 7 d) and which are not.
S11. Error codes: `TURN_EXPIRED` (410; ADR-025 R49, 06 §6.6 `SSE_REPLAY_TTL_S`) and `TENANT_NOT_FOUND` (06 §6.1 table) are missing from the 06 §6.1 "Error codes" list.
S12. `acl.changes.v1` payload `AdvisorEntitlementChanged {advisor_id, ...}` (06 §6.4 line 71) puts a subject id on Kafka; ADR-029 and 05-1 §5.12 require `pseudonym_id` only. Change to `pseudonym_id`.
S13. `fund_rr_facts` (04-2 §4.15, 11, plan E11) has no table definition in 05/05-1 and no owner in E1 or E11 table lists; the `sec` connector emits two source classes (RR facts: "public data, retire"; 497K: `publisher`) while `source_registry.source_class` and the `Connector` Protocol allow one of `law|qa|fca_api|publisher`. Define the table and the class for RR facts (likely `law`).
S14. Table ownership gaps in plan E1/E11-E13: `erasure_receipts`, `reconciliation_manifests`, `reconciliation_findings`, `pseudonym_map` (E1 lists the mapping table only in prose) are not named as owned by any epic; E1's R4 list omits them.
S15. plan E4: edge case #10 appears in the change list (line 201) but not in the "Added to Done when" bullet (line 203); add it. plan E7 "Arch sections" line cites ADR-017, ADR-016, ADR-008 but not ADR-037, which E7 owns.
S16. ADR-018 and ADR-002 keep the trigger "real firm data" with no amendment; ADR-038 says it amends ADR-018 but decision-r4.md lists seven amended ADRs (009, 013, 014, 015, 016, 017, 022), and no "Amended 2026-11-02" block exists on ADR-018. Add the block (or drop the claim from ADR-038).
S17. Residency wording is incomplete: ADR-038, 08 §8.7 and architecture.md §8 say "Data at rest ... stays in the tenant's home cell" with no exception, while ADR-031 and plan E13 list global data (user id, email, firm membership, tenant-to-cell map, PUBLIC manifest hashes, aggregate metrics) for the privacy notice, ADR-032 says identity data location is unknown, and Cloud Logging, Cloud Trace and Monitoring are single-region. Add "except the declared global data (ADR-031)" to the ADR-038 wording and to 08 §8.7.
S18. deep-dive/00-as-built-baseline.md mermaid blocks 3 and 4 do not parse: unescaped `;` inside sequence messages (`A->>D: autobegin; SET ROLE finadvisor_app; ...` line 12 of block 3; `S->>D: BEGIN; INSERT documents ...; COMMIT` line 18 of block 4). Replace `;` with `#59;` or commas. Historic file, low risk.
S19. architecture-diagram.md edge `SILVER -->|"embed"| VOY` conflicts with 04 §4.7 line 145, 04-1 Flow 2 and architecture.md §5: the indexer embeds, not the silver worker. Move the edge to `IDX`.
S20. Tombstone invariant scope differs: ADR-030 and 09 §9.7 include Langfuse ("Postgres, GCS, BigQuery (current), Langfuse and the cache"); 04-2 §4.22 table and 02 §2.9 omit Langfuse. Align.
S21. ADR-028 step order vs R4-D5: ADR-028 and plan E6 line 252 list "bump the tenant `corpus_version` row last, purge cache rows, write `processed_events`" (the bump is not last in that list); 04-2 §4.17 has cache purge (5), `processed_events` (6), bump (7). Also 04-2 §4.17 says "ONE transaction per document version" where D5 says one document per transaction. Use the 04-2 order and "per document".
S22. The state.md "Validation verdicts not yet folded" are still unfolded: BigQuery `default_max_time_travel_hours = 48` at project level (V-docs-db.md: dbt-bigquery does not document the dataset option, so "enforced on every dataset including dbt-created ones" has only an assertion, no mechanism; add the project default to ADR-029, 05-1 §5.14, 11 and E10), Model Armor "behind a flag, with a fallback" (arch has fail closed with `MODEL_ARMOR_FAIL_OPEN=false` only), Voyage `llm_egress_ack` wording (opt-out, no region). They are decision inputs, not drift, but the stage-4 plan must not ship with them unrecorded.
S23. 08 §8.2 item 4 ("tenant-aware verify with `auth_for_tenant(tenant_id)`") and item 8 / ADR-032 ("server verifies at project level, reads `firebase.tenant`, checks it equals the URL tenant") describe two verification procedures; pick the ADR-032 one in item 4 and 04-1 Flow 1.
S24. Config key drift: ADR-025 R82 names `KONG_VALKEY_HOST` / `KONG_VALKEY_PORT`; 06 §6.6 has only `VALKEY_INSTANCE_NAME` ("endpoint passed to Kong as an env var"). ADR-025 R78 says demo PITR off and prod PITR 7-day logs while ADR-029 and 10 item 14 call PITR log days UNVERIFIED; 05-1 §5.14 documents backups 7 d only. Add the two Kong keys to 06; reword R78 as an ESTIMATE.

## Notes for the plan stage (no action needed in arch)
- epic/ has folders E0-E10 only; E11-E13 folders and tickets do not exist yet (expected: stage 4).
- plan.md Done-when for #6 uses tier N (nightly) and 07 uses "nightly": consistent.

## Hidden assumptions
- The first-stage target (300 ms) assumes a warm query-embed call of about 0.1 s; nothing measures Voyage embed latency from Cloud Run.
- The 24 h live-store promise assumes the erasure job runs first at every demo start and finishes before traffic; no timing is stated for a large tenant erase.
- "Per-document advisory lock" assumes `hash(tenant_id, doc_id)` never collides across tenants (a collision serialises two documents but cannot corrupt; still unstated).
- The pull/push question in M6 assumes `fa_etl_public` is the only way to enqueue per-firm erasure; no alternative role exists.
- 200 items at exactly 5 per cluster (S7) assumes the first corpus yields 40 usable provisions or products.

## Most dangerous problem
FCA-licensed text can persist in Kafka and BigQuery through chat.audit and eval.sample events although the arch (and the FCA revocation purge) assumes it never does (M5), so a revocation would leave unpurged copies in two stores with no erase step.
