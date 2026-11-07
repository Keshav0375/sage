# Round 4 stage 4: ticket changes for E4, E5, E6

Date 2026-11-07. No ticket was closed (no whole ticket became obsolete); the E4-T24 delete path is removed inside that ticket.

| key | action (keep-changed/new/close) | reason |
|---|---|---|
| E4-T1 | keep-changed | Timeout from measured Cloud Run latency, 150 ms rule, flag default (ADR-036/009 amended, R4-D18 V3) |
| E4-T2 | keep-changed | Measure DE/FR recall, English-only claim (ADR-036 decision 7) |
| E4-T4 | keep-changed | Model Armor flag keys, FAIL_OPEN removed, ENTITLEMENT_CHANGED, contextual flag off (ADR-036, ADR-016) |
| E4-T6 | keep-changed | Model-retirement guard #10, no temperature/top_p/top_k (ADR-039, 07 §7.4) |
| E4-T9 | keep-changed | Model Armor behind MODEL_ARMOR_ENABLED, fallback, fail-open prompts (ADR-036 amended, R4-D18 V3) |
| E4-T11 | keep-changed | as_of valid_range post-generation check, original-text compare (ADR-027, ADR-036) |
| E4-T18 | keep-changed | as_of resolver, echo, locale date rule, meta as_of (ADR-027, R4-D4, R4-D20) |
| E4-T19 | keep-changed | Per-request nonce, ReleaseCheck pipeline, original-text compare (ADR-036, ADR-009 amended) |
| E4-T21 | keep-changed | chat.audit and eval.sample carry no text, pseudonym_id (ADR-013 amended, R4-D19 M5) |
| E4-T24 | keep-changed | Drop document delete via acl_change_requests; deletes go to deletion_requests, E12-T11 (ADR-022 amended, ADR-029) |
| E4-T26 | keep-changed | Model Armor timeout now fails open via fallback with audit flag (ADR-036 amended) |
| E4-T27 | keep-changed | TTFT measured to first complete sentence (ADR-036, ADR-039 M3) |
| E4-T28 | new | Numeric grounding gate, locale-aware, Hypothesis tests (ADR-036) |
| E4-T29 | new | Licence footer, jurisdiction label, staleness by state (ADR-036 decision 5) |
| E4-T30 | new | Role policy as data, default deny, generated matrix (ADR-036 decision 6) |
| E4-T31 | new | Entitlement re-read, ENTITLEMENT_CHANGED, message refused (ADR-033, #2) |
| E4-T32 | new | llm_egress_ack enforced on the Anthropic/Voyage query path (ADR-038, ADR-039 V4) |
| E4-T33 | new | calc tool required by the numeric gate and policy table (ADR-036) |
| E5-T2 | keep-changed | Delete-policy topics: retention 7 d, segment.ms 1 d, editability spike (ADR-013 amended, ADR-029) |
| E5-T4 | keep-changed | chat.audit and eval.sample payloads carry no text; pseudonym_id on subject events (ADR-013 amended, R4-D19 M5) |
| E5-T5 | keep-changed | BACKWARD contracts for docs.* and chunks.* checked in CI (ADR-013 amended, ADR-034) |
| E5-T6 | keep-changed | Producer rejects fca_api source; FCA content never on Kafka (ADR-013 amended, ADR-026) |
| E5-T11 | keep-changed | Polling worker on acl_change_requests, no Kafka, lock order (ADR-022 amended, ADR-028, R4-D7) |
| E5-T12 | keep-changed | Add the stop-Kafka, tighten-ACL, refused-within-60-s test (ADR-022 amended) |
| E5-T13 | keep-changed | Delete-policy topic settings, no applier ACL (ADR-013 amended, ADR-022 amended, ADR-029) |
| E5-T14 | keep-changed | Sink guard dependency, no text/FCA in BigQuery, acl.changes analytics only (ADR-028, ADR-013 amended) |
| E5-T15 | new | New: uncached ledger point-read helper for every sink (ADR-028, R4-D20) |
| E6-T5 | keep-changed | Chunk identity fields valid_from and parser_version, B0 structural prefix (ADR-027, ADR-016 amended) |
| E6-T6 | keep-changed | Versioned silver path, Pandera SCHEMA_AND_DATA (ADR-014 amended, ADR-034) |
| E6-T7 | keep-changed | Sink guard before and after Parquet write, versioned path (ADR-028, 4.7) |
| E6-T8 | keep-changed | Contextual headers default OFF, B0 prefix kept, sink guard (ADR-016 amended, ADR-028) |
| E6-T10 | keep-changed | Atomic per-document publish, lock order, gates (ADR-028 amended, R4-D5, 4.17) |
| E6-T21 | new | Chunk identity 8-column key, reuse index, generations keyed on identity (R4-D19 M1, ADR-035) |
| E6-T20 | new | Ingest scan stage: sanitiser, pattern list, quarantine (ADR-036, ADR-034, 4.25) |
| E6-T11 | keep-changed | Replay after parser bump, polling applier ACL test (ADR-027, ADR-022 amended) |
| E6-T13 | keep-changed | In-process path uses scan stage, atomic publish, ledger guard; no FCA on Kafka (ADR-028, ADR-026) |
| E6-T14 | keep-changed | Scan includes FCA marker and no answer text in Kafka/BigQuery (test #15, ADR-013 amended) |
| E6-T15 | keep-changed | dbt contract enforced on gold tables (ADR-014 amended, ADR-034) |
| E6-T17 | keep-changed | Project default max time travel 48 h plus per-dataset check (ADR-029 amended, R4-D18 V2) |
| E6-T18 | keep-changed | Ledger-guarded ingest mapping, no FCA/text, dbt sets no dataset options (ADR-029 amended, ADR-028) |
| E6-T19 | keep-changed | Assert 48 h time travel on every dataset incl. dbt-created (ADR-029 amended) |

Counts: keep-changed 32, new 9, close 0.

## Questions and flags

1. Task text says the `acl.changes` topic is removed; ADR-022 amended, 6.4 and plan keep `acl.changes.v1` for analytics (applier no longer consumes it). Tickets follow the arch: topic stays, applier polls Postgres.
2. E5-T15: how does the bq-sink map events without `sha256` (chunks.indexed, chat.*) to a ledger key `(doc_key, sha256)`? Does a tombstone match any sha256 for a doc_key, or only the stored one? Ticket applies the guard only where a document reference exists. Also: `fa_etl_public` has no grant on `erasure_ledger` (E12-T5 grants `fa_worker` only); E6-T13 needs a SELECT grant for the in-process guard.
3. E4-T28: when sentence N fails the numeric gate, sentences 1..N-1 are already released (sentence-level release). Arch says 'withholds the answer'. Ticket stops emission and sends refusal after earlier deltas; confirm or require holding the whole answer.
4. E4-T33: the arch lists a `calc` tool (8.6, 8.8) but 6.3 and E4-T10 define four tools and no calc argument shape; the `{operation, operands}` shape is invented and needs ratification.
5. E4-T32: ADR-038 requires `llm_egress_ack` before private ingest; a query-time refusal for private chunks (code `LLM_EGRESS_NOT_ACKNOWLEDGED`) is derived from 'proved by ... all three paths'. Confirm the runtime behaviour and code name.
6. E4-T11 (not T18) holds the post-generation valid_range check and E4-T28/T29/T31/T32/T33 split the numeric gate, footers, entitlement, egress and calc out of E4-T18, because T18 would exceed size M. E4-T18 keeps the as_of resolver, meta/notice echo and the pre-LLM flow.
7. E11-T13 (Model Armor document screening) should depend on E6-T20 (scan stage, new) and E4-T9 (now carries mode `document`); E11 tickets E11-T9 and E11-T23 depend on E6-T10, which is now the publish transaction (the diff there is replaced by E11-T9 reconcile_lineage). E12-T8 and E6 sinks depend on E5-T15 as required; E12-T8 itself still needs the dependency added.
8. The `pseudonym_id` source for outbox payloads (E4-T21) is assumed to be the Principal via E1-T23; confirm the Principal carries it.
9. `source_observations` is called a Schema Registry contract in plan E5 but has no topic in 6.4; E5-T5 registers docs.* and chunks.* only.
10. `provision_path` (E6-T5) is assumed to be the structural section path of the chunker; the arch names the column in the identity key but not its derivation.
