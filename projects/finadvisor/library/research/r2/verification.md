# Verification of the as-built maps (2026-11-01)

## Skeptic (independent re-read of the code)
Confirmed: 1 header-only auth (backend/src/auth/jwt.py:9-13; python-jose unused; jwt_secret unused) · 3 RLS only on chunks (schema.sql:61-71) · 4 suitability_rules never ingested (ingest.py:130-228 only documents/chunks; only tests/test_lookup_suitability.py:67 inserts) → lookup_suitability_rule empty on a real DB · 5 re-ingest not idempotent (ingest.py:127,149,200-228) · 6 lookup_factsheet returns unredacted raw_content (lookup_factsheet.py:58,83; ingest.py:141) — PII leak to LLM, not a tier leak · 7 no citation events produced; tool/tool_result SSE events unredacted (chat.py:54-70) · 8 queries embedded with input_type="document" (embeddings.py:46) · 9 no frontend/Dockerfile; override targets missing `dev` stage · 10 CI `pip install -e ".[dev]"` but Poetry pyproject has no `dev` extra → ruff/mypy/pytest not installed → CI broken as written · 11 Kong http-log → /api/audit/kong, route missing · 12 Terraform: backend KONG_URL=localhost:8000 (calls itself), allUsers invoker on backend+frontend, Cloud SQL public IP no private network, backups/HA prod-only, Langfuse DB never backed up · 13 ci.yml has no Postgres service → DB tests skipped · 14 SSE generator and messages.create unguarded → mid-stream failure drops connection with no error event.

PARTLY (claim 2, RLS context): rls.py:11 does SET ROLE finadvisor_app first and chunks has FORCE RLS, so RLS IS enforced on the normal path. tier is int()-cast; only jurisdictions are raw strings (from MOCK_USERS today). Plain SET is reverted by the rollback that ends each read-only request (no commit anywhere in src) — safe today by accident; breaks as soon as a commit is added. reset_rls_context only RESETs ROLE, not app.* GUCs.

New hidden risks:
- Cloud SQL user `finadvisor` (cloud_sql.tf:33) is cloudsqlsuperuser, not a true superuser; no GRANT finadvisor_app TO finadvisor; Terraform never applies schema.sql → SET ROLE likely fails or roles do not exist → cloud backend probably fails on first RLS call (inferred).
- Kong upstream http://litellm:4000 is Docker DNS, invalid on Cloud Run.
- Most dangerous: spoofable X-User-Id + allUsers invoker on Cloud Run → anyone can read Tier-4 UK content; plus documents/suitability_rules without RLS and unredacted raw_content in tool_result events.

## Docs: pgvector 0.8.7 README, PostgreSQL 16.15, Voyage (read 2026-11-01)
- IVFFlat must be created after data ("Create the index after the table has some data"); lists ≈ rows/1000; probes default 1, start at sqrt(lists). HNSW: better speed-recall, can be built on an empty table. At 114 rows a sequential scan is exact.
- ANN filtering is applied after the index scan (README: 10% selectivity with ef_search 40 → ~4 rows). RLS predicates behave as such filters (README silent on RLS specifically). Mitigations: iterative index scans (pgvector ≥0.8.0: hnsw.iterative_scan strict_order/relaxed_order, hnsw.max_scan_tuples 20,000, ivfflat.max_probes), higher ef_search, partial indexes or partitioning. Deployed pgvector version unknown — check `SELECT extversion FROM pg_extension WHERE extname='vector'`.
- PostgreSQL: superusers and BYPASSRLS always bypass RLS, FORCE does not change that; SET ROLE to a non-superuser drops superuser privileges. Session SET persists after COMMIT, reverted on ROLLBACK. Recommended: one transaction per request with set_config(name, value, true) (bind parameters) and SET LOCAL ROLE; connect as a non-superuser, non-owner role. current_setting without missing_ok raises (policy errors → 500, fail closed).
- Voyage: specify input_type ("query" for queries); voyage-3 is older generation (current voyage-4 series; voyage-finance-2 for finance); voyage-3 1024 dims only; Tier-1 rate limit 2000 RPM (code throttles to ~180 RPM); list max 1,000; backoff with jitter recommended. Pricing voyage-3 $0.06/1M.

## Docs: LiteLLM (docs.litellm.ai, unversioned, read 2026-11-01)
- Same model_name deployments are load-balanced; simple-shuffle without rpm/tpm/weight picks randomly → ~1/3 Claude, 1/3 GPT-4o, 1/3 Gemini-Flash while Claude is healthy (inference from quotes). Silent model substitution under the "claude-sonnet-4" name.
- fallbacks are keyed by model_name group; `claude-primary` is a model_info.id → fallback entry most likely matches nothing.
- Documented patterns: `order` in litellm_params (1 = primary) within one group, or separate model_names chained by `fallbacks`.
- No timeout set → library defaults (undocumented in pages read). Options: router timeout, litellm_params timeout / stream_timeout, litellm_settings.request_timeout.
- cooldown_time 300 benches the sole primary 5 min after >3 fails/min (default 5 s).
- Pin a SemVer tag, not main-latest. Redis required for >1 instance (shared cooldown, rate limits, budgets); Postgres for virtual keys/spend tracking.
- Anthropic SDK against the proxy /v1/messages is supported ("follows the Anthropic messages specification"), key as x-api-key. Kong passthrough of x-api-key and SSE untested.
- drop_params true may silently drop Anthropic-specific params on fallback (unverified).

## Keshav's inputs for future research (2026-11-01)
- Scope of this run: map the as-built MVP only, as the baseline for later research. No target design yet.
- Scale ~50 advisors, <5 QPS. Budget < $100/month cloud + LLM. Compliance: as MVP — US/EU/UK synthetic corpus (FINRA, SEC, MiFID II, FCA COBS as encoded); no real regulatory certification.
