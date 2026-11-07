# Round 4 stage 4: ticket changes for E0 to E3 (2026-11-07)

| key | action | reason |
|---|---|---|
| E0-T13 | keep-changed | CI asserts Postgres major 16 equals Cloud SQL and the PR gate stays under 12 min (ADR-027, ADR-017) |
| E0-T15 | new | Test helpers: VCR-style HTTP replay, race harness, Kafka-off fixture (ADR-017, ADR-026, ADR-028) |
| E1-T4 | keep-changed | `tenants` gains cell_id, residency_class, source_epoch; same idp_uid allowed in two tenants (ADR-031, ADR-032) |
| E1-T5 | keep-changed | btree_gist, 8-column chunk identity, range columns, per-leaf EXCLUDE; 3-column key becomes plain index (ADR-027, ADR-035, R4-D19 M1) |
| E1-T11 | keep-changed | Onboarding takes cell_id and residency_class, asserts the per-leaf EXCLUDE, seeds pseudonym_map (ADR-027, ADR-031, ADR-029) |
| E1-T13 | keep-changed | Gated by the same-email spike (E1-T22); one token per firm, no identity merge (ADR-032, R4-D18 V5) |
| E1-T17 | keep-changed | New invariant: every chunks leaf has the EXCLUDE constraint and btree_gist exists (ADR-027) |
| E1-T19 | keep-changed | Leak matrix: fa_etl_public writes no firm table, new tables enter by pg_class (ADR-039 M6, ADR-002 D13a) |
| E1-T21 | keep-changed | One IdP tenant per firm, gated by E1-T22 (ADR-032) |
| E1-T22 | new | Spike: same email in two Identity Platform tenants, gates the IdP tickets (ADR-032, R4-D18 V5) |
| E1-T23 | new | pseudonym_map plus pseudonym_id on conversations and messages, RLS; deleting the mapping unlinks (ADR-029, ADR-038, R4-D6) |
| E2-T8 | keep-changed | Per-cell hostnames and ALB host rules in the URL map (ADR-031) |
| E2-T12 | keep-changed | Adds the public `GET /resolve` Kong route (ADR-031, R4-D20) |
| E2-T14 | keep-changed | Per-IP rate limit on `/resolve` (ADR-031) |
| E2-T22 | new | Spike: ALB host rules for per-cell hostnames, with cost (ADR-031) |
| E3-T1 | keep-changed | Default reranker rerank-3-lite, rerank-3 comparison, rerank-2.5 removed (ADR-039 V1, ADR-037) |
| E3-T2 | keep-changed | Spike adds 30% superseded rows, strict vs relaxed order, HNSW build time, first-stage p95 <= 600 ms (ADR-027, ADR-039 M3) |
| E3-T4 | keep-changed | (tenant_id, chunk_hash, embed_model) is a non-unique reuse index (ADR-035, R4-D19 M1) |
| E3-T5 | keep-changed | `search` takes as_of, inlines embed_model literal from allow-list, merges adjacent ranges (ADR-027, ADR-035) |
| E3-T6 | keep-changed | RERANK_MODEL default rerank-3-lite, config-only so ablation arm 3 needs no code (ADR-037, ADR-039) |
| E3-T8 | keep-changed | expand_parents and fetch_chunks take as_of and carry the predicate (ADR-027) |
| E3-T9 | keep-changed | `retrieve` takes and returns as_of (ADR-027) |
| E3-T13 | keep-changed | Cache key adds as_of, embed_model, PUBLIC source_epoch (ADR-015 amended, ADR-027, ADR-035) |
| E3-T14 | keep-changed | Hit also requires every cited chunk valid at as_of; miss after a new version (ADR-015 amended, ADR-027) |
| E3-T15 | keep-changed | Purge on publish, supersede, retire, withdraw, erase; document delete is the erasure-worker's (ADR-015 amended, ADR-039 M7) |
| E3-T16 | keep-changed | First-stage gate p95 <= 600 ms, rerank-3-lite default (ADR-039 M3, V1) |
| E3-T17 | new | CI check: SQL on chunks and document_versions in retrieval carries the as_of predicate (ADR-027) |
| E3-T18 | new | As-of boundary-day test #9: day edges, clock +/-2 h, DST days (ADR-027) |

Counts: keep-changed 22, new 6 (E0-T15, E1-T22, E1-T23, E2-T22, E3-T17, E3-T18), close 0.

Open questions and assumptions are in the stage report.
