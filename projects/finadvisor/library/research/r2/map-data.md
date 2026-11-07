# FinAdvisor as-built map: data layer and RAG (Explore, 2026-11-01)

Paths relative to /Users/keshav/Projects/FinAdvisor. "inferred" = not confirmed in code.

## 1. Schema (backend/db/schema.sql, raw SQL, no migrations)
- Applied as initdb mount (docker-compose.yml:2,12) — first init only; CI `psql -f db/schema.sql` (eval-gate.yml:69). No alembic, no version table.
- Extensions vector, pgcrypto (:6-7).
- documents (:12-29): id UUID PK gen_random_uuid; title; doc_type CHECK 4 values; jurisdiction CHECK (US,EU,UK,APAC); tier_required INT CHECK 1..4 default 1; regulatory_ref; last_reviewed_at DATE; product_category; risk_level CHECK (conservative, moderate, aggressive); raw_content TEXT (un-redacted); created_at.
- chunks (:34-46): id; document_id FK ON DELETE CASCADE; chunk_index; content; embedding vector(1024) NOT NULL; denormalised jurisdiction, tier_required, regulatory_ref, last_reviewed_at, source_title (no CHECKs on chunk copies).
- suitability_rules (:95-108): id, rule_name, product_category, client_risk_profile CHECK 3 values, min_tier_required, jurisdiction, regulatory_ref, rule_text, last_reviewed_at, created_at.
- Indexes: IVFFlat vector_cosine_ops lists=10 (:51-52), built on empty table (centroids untrained, inferred); no HNSW; no ivfflat.probes anywhere. Btree chunks(document_id), chunks(jurisdiction), chunks(tier_required) (:54-56). Nothing else on documents/suitability_rules.

## 2. Row-level security
- Only chunks: ENABLE + FORCE (:61-62). documents and suitability_rules have none.
- Policy chunk_visibility FOR SELECT (:64-71): tier_required <= current_setting('app.user_tier')::int AND jurisdiction = ANY(string_to_array(current_setting('app.user_jurisdictions'), ',')). No missing_ok → unset var errors (fails closed).
- Roles finadvisor_service (ALL), finadvisor_app (SELECT) on three tables (:76-111), NOLOGIN. App connects as superuser finadvisor (src/config.py:19; src/db/rls.py:10). Service role unused.
- Per request: src/db/rls.py:9-17 SET ROLE finadvisor_app; SET app.user_tier; SET app.user_jurisdictions — f-string, jurisdictions unvalidated list[str] (src/auth/models.py:10). Plain SET not SET LOCAL; reset never called; pooled-connection safety depends on rollback (inferred).
- Wired via get_rls_session (src/dependencies.py:33-38) → get_agent (57-68).
- lookup_factsheet / lookup_suitability filter in SQL (src/agent/tools/lookup_factsheet.py:56-65; lookup_suitability.py:61-70).
- Isolation tests (require live DB, conftest.py:38-41): test_rls.py (19,39,53), test_rls_context.py (15,31), test_rls_e2e.py:46-111 (top_k=200, assert_zero_leakage for 4 users). Fixture duplicates policy text (conftest.py:72-125); TEST_DATABASE_URL is the dev DB (conftest.py:17); create_all fixture would create tables without RLS/index (conftest.py:50).

## 3. ORM and sessions
- src/db/models.py SQLAlchemy 2.0 Document, Chunk, SuitabilityRule, Vector(1024) (:42); no CHECKs/indexes; only used for test create_all. Runtime and ingest use raw text() SQL.
- Async engine asyncpg pool_size 5 max_overflow 10 expire_on_commit False (src/db/session.py:9-15), no pool_pre_ping/recycle/statement timeout. One AsyncSession per request (dependencies.py:27-30), no commits (read-only).
- Ingest: own engine, one transaction session.begin() (scripts/ingest.py:200-228).

## 4. Ingest
- Source data/corpus/{product_factsheets,suitability_rules,compliance_memos,jurisdiction_disclosures}/NN_slug.json; rglob (scripts/ingest.py:89-96).
- Generator backend/scripts/generate_corpus.py: 50 specs (20/10/10/10) with stale and pii flags; Claude claude-sonnet-4-20250514 (:667), max_tokens 2048, 300-800 words; 8 docs with fake PII.
- Chunking: custom recursive splitter CHUNK_SIZE 2048 chars, OVERLAP 200 (ingest.py:23-86); overlap prefix can exceed 2048.
- PII before chunking: RegexRedactor (src/pii/fallback.py:24-29) SSN, PHONE, EMAIL, ACCOUNT (8-12 digits); no names/addresses. Optional DLP (src/pii/redactor.py:26-46) PERSON_NAME, PHONE, EMAIL, US SSN, CA SIN, FIN ACCOUNT, CREDIT CARD, STREET_ADDRESS, LIKELY; sync per doc, no retry.
- Embeddings (src/retrieval/embeddings.py): voyage-3, 1024, batch 128, 3 retries exp backoff base 1s, 3 concurrent / 3 RPS; sync client in to_thread; no timeout; embed_query uses input_type="document" (:34-47). Cost $0.06/1M hard-coded (ingest.py:181).
- Metadata: documents all fields + raw_content unredacted (ingest.py:141); chunks get jurisdiction, tier, regulatory_ref, last_reviewed_at, source_title — not doc_type, product_category, risk_level.
- NOT idempotent: uuid4 per run, plain INSERT, no unique source key (ingest.py:127,149); _source_file loaded but not stored.
- suitability_rules never populated by ingest (only a test inserts, tests/test_lookup_suitability.py:67) → lookup_suitability_rule returns empty on a real DB (inferred).
- --target test swaps /finadvisor → /finadvisor_test (ingest.py:197-198).

## 5. Retrieval
- search_firm_kb → embed_query → VectorStore.similarity_search (src/retrieval/vector_store.py:16-45): ORDER BY embedding <=> :vec LIMIT top_k, score 1 - distance. No WHERE (RLS only), no threshold, no rerank, no hybrid/BM25. IVFFlat + post-filter RLS can return fewer than top_k (inferred).
- Citations: results (chunk_id, content, source_title, regulatory_ref, last_reviewed_at, similarity) go to the LLM; system prompt requires [n] (src/agent/system_prompt.py:12,24); no server-side citation map; CitationEvent never produced.

## 6. Sizes
- 50 docs, ~187,840 chars (~47k tokens). ~114 chunks (docs/demo_script.md:9). APAC only in 2 disclosures.
- Golden QA data/eval/golden_qa.json: 50 items (suitability 15, jurisdiction 10, refusal 10, citation 10, stale 5); fields id, category, user_profile, question, expected_behavior, must_cite_refs, must_not_contain, expected_tool_calls. Judge data/eval/judge_prompt.txt, judge model claude-sonnet-4-20250514 (scripts/run_eval.py:23). Gate citation ≥0.95, faithfulness ≥0.90. No retrieval metrics (recall@k, MRR).

## 7. Gaps
- No migrations/versioning. IVFFlat lists=10 on empty table, no probes; HNSW better at this scale; no filtered-ANN strategy for RLS.
- Re-ingest duplicates. suitability_rules has no ingest path.
- Superuser connection + SET ROLE; SET not LOCAL; f-string SET values unvalidated.
- RLS only on chunks; a code path without get_rls_session would leak (superuser bypasses RLS).
- Query embedding wrong input_type; no timeout; retry catches all exceptions.
- Hard-coded model, dimension, chunk size, pool sizes, price.
- PII: documents.raw_content unredacted and returned to the LLM by lookup_factsheet (lookup_factsheet.py:83); regex misses names/addresses; ACCOUNT pattern over-matches; per-event output redaction misses split PII (chat.py:46-52).
- Tests mutate the dev DB; policy text duplicated.
- No backup/retention locally. No server-side citation mapping. No retrieval eval, reranker, cutoff, pool_pre_ping, statement timeouts.
