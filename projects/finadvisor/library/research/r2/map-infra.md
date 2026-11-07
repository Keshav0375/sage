# FinAdvisor as-built map: infra, gateway, CI, ops (Explore, 2026-11-01)

Paths relative to /Users/keshav/Projects/FinAdvisor. DC = docker-compose.yml, OV = docker-compose.override.yml. "inferred" = not read directly.

## 1. Local runtime
- postgres `pgvector/pgvector:pg16` (DC:3), 5432:5432 (DC:8-9), volume pgdata + backend/db/schema.sql as init (DC:10-12), healthcheck pg_isready (DC:13-17), creds `localdev` hardcoded (DC:5-7).
- backend build ./backend (DC:20), 8000:8000 (DC:21-22); env DATABASE_URL, KONG_URL=http://kong:8000, LANGFUSE_HOST=http://langfuse:3000, VOYAGE/ANTHROPIC/LITELLM keys, PII_MODE=regex, JWT_SECRET default `[dev secret, redacted]` (DC:24-31); depends_on postgres healthy, kong started (DC:32-36). No LANGFUSE keys passed → tracing off in compose (backend/src/main.py:55 needs both).
- frontend build ./frontend, 3000:3000, NEXT_PUBLIC_API_URL=http://localhost:8000 (DC:39-45). **No frontend/Dockerfile exists** → cannot build.
- litellm build ./litellm, 4000:4000, provider keys + master key (DC:48-55), no healthcheck.
- kong build ./kong, host 8001→8000, KONG_DATABASE=off, declarative config (DC:58-65), depends_on litellm without health condition.
- langfuse `langfuse/langfuse:2` 3030:3000, DB langfuse-db (DC:68-79); SALT missing (standalone file sets it, langfuse/docker-compose.langfuse.yml:10).
- langfuse-db `postgres:16` 5433:5432, creds langfuse/langfuse (DC:82-95).
- redis `redis:7-alpine` 6379 (DC:98-102) — unused by any config (inferred).
- OV: backend `target: dev` but backend/Dockerfile is single-stage (no such target) (OV:3-5); src/tests mounts, uvicorn --reload, LOG_LEVEL=debug (OV:6-11); frontend npm run dev (OV:13-18).
- Fixed host ports: 5432, 8000, 3000, 4000, 8001, 3030, 5433, 6379.
- langfuse/docker-compose.langfuse.yml duplicates langfuse services, init user [dev default login, redacted], keys [dev key, redacted]/[dev key, redacted] (:11-17); conflicts on ports 3030/5433.

## 2. Kong (kong/kong.yml, kong/Dockerfile)
- `kong:3.9` DB-less, config baked via COPY (Dockerfile:1-10).
- One service llm-service → http://litellm:4000, route /v1 (kong.yml:3-10).
- Global plugins: rate-limiting 60/min, 500/h, policy local, keyed on `X-User-Id` header (spoofable) (:13-19); request-size-limiting 1 (MB, inferred); http-log → http://backend:8000/api/audit/kong (:25-29) — **route does not exist** in backend (backend/src/api/router.py:8-10).
- No auth plugin, no ai-proxy, no CORS. Plain reverse proxy + rate limit.
- Backend calls LLM via kong_url/v1 with litellm_master_key using the Anthropic SDK (backend/src/main.py:45-49); LLM_BASE_URL bypasses Kong (backend/src/config.py:29).

## 3. LiteLLM (litellm/config.yaml)
- `ghcr.io/berriai/litellm:main-latest` (floating) (Dockerfile:1).
- Three deployments share model_name `claude-sonnet-4-20250514`: claude-primary (anthropic), gpt4o-fallback (openai/gpt-4o), gemini-fallback (gemini/gemini-2.5-flash) (config.yaml:1-21).
- Router: simple-shuffle, num_retries 2, retry_after 5, fallbacks claude-primary → [gpt4o, gemini], allowed_fails 3, cooldown 300 (:23-30). **Likely defect**: shared model_name + shuffle may spread traffic across providers instead of Claude-first; fallbacks reference deployment ids (inferred).
- drop_params true; no timeout, budget, cache, DB (:32-37).
- Backend DEFAULT_MODEL claude-sonnet-4-20250514 (backend/src/agent/orchestrator.py:18). Tests: backend/scripts/test_fallback_live.py, backend/tests/test_fallback_chain.py.

## 4. LangFuse
- v2 major tag (DC:68; terraform/cloud_run.tf:289), own Postgres. SDK init only if both keys (backend/src/main.py:50-59; config.py:32-35); tracing + prompt fetch with fallback (backend/src/observability/tracing.py:11-89).

## 5. Terraform GCP
- State: GCS `finadvisor-tfstate` prefix terraform/state, bucket not managed, one prefix for all envs (main.tf:11-14). google ~>5.0; `random` provider undeclared.
- us-central1, env default dev (variables.tf:6-16).
- Cloud Run v2: backend min 1 (prod)/0, max 10, 1 CPU 512Mi, Cloud SQL socket (cloud_run.tf:8-17,114-117); frontend min 0 max 5 256Mi (no Dockerfile); litellm max 3; kong max 3; langfuse max 2. No concurrency/timeout settings, no VPC egress.
- Cloud SQL app: POSTGRES_16, db-f1-micro, REGIONAL + backups + PITR + deletion_protection **only in prod** (cloud_sql.tf:1-26), pgvector flag. Langfuse DB: f1-micro, no backups/HA, deletion_protection false (:56-70). **Both public IPv4**, no private networking.
- Secret Manager: db-url, anthropic, openai, google, voyage, litellm-master, jwt-secret, langfuse public/secret; only db_url populated by TF.
- IAM: SAs for backend and frontend only; backend roles project-wide (secretAccessor, cloudsql.client, dlp.user, storage.objectViewer) (iam.tf:11-33); `allUsers` invoker on backend and frontend (iam.tf:35-49).
- Artifact Registry repo `finadvisor`; GCS corpus (versioned) and eval-results buckets.
- **Cloud wiring broken**: backend KONG_URL=http://localhost:8000 (cloud_run.tf:44-47); Kong upstream litellm:4000 is a Docker DNS name; no service-to-service IAM. NEXTAUTH_SECRET "changeme-in-production" hardcoded (cloud_run.tf:314-317), DB password plaintext env (:302-312). Image tags default `latest` (variables.tf:24-46).
- Not deployed: Redis, VPC, LB, Cloud Armor, monitoring/alerting/uptime checks.

## 6. CI (.github/workflows)
- ci.yml (PR + push main): backend ruff check, ruff format --check, mypy src/, pytest tests/ (Py 3.12); frontend npm ci, lint, tsc --noEmit, build (Node 20). **No Postgres service** → DB tests cannot run (inferred).
- eval-gate.yml (PR to main): duplicate lint/test; eval job with pgvector service, schema load, `scripts/ingest.py --target test`, uvicorn + sleep 5, `scripts/run_eval.py`; fails below avg_citation_accuracy 0.95 or avg_faithfulness 0.90 (:97-114); secrets ANTHROPIC, VOYAGE, LANGFUSE keys. No KONG_URL/LLM_BASE_URL → defaults to localhost:8001 with no Kong (eval may fail, inferred).
- Packaging risk: CI `pip install -e ".[dev]"` but pyproject is Poetry with dev group, no `dev` extra (inferred: dev tools may be missing). Dockerfile same.
- Missing: image build/push, deploy, terraform plan/apply, dependency/container/secret scans, CodeQL, Dependabot, coverage gate, frontend tests, compose integration job, pre-commit. Eval gate says "DEPLOY BLOCKED" but no deploy exists.

## 7. Secrets and config
- .env gitignored and untracked; .env.example committed with placeholders and dev defaults (LITELLM_MASTER_KEY=[dev key, redacted], JWT_SECRET=[dev secret, redacted]).
- Dev creds committed in compose files.
- App config defaults to dev secrets → missing prod env var falls back silently (backend/src/config.py:13,36-37).
- Cloud Run secrets via secret_key_ref version "latest".

## 8. Production gaps (summary)
Frontend Dockerfile missing; override bad target; backend image root, single stage, no .dockerignore/HEALTHCHECK; floating tags; cloud runtime cannot reach Kong/LiteLLM; Cloud SQL public IP; HA/backups prod-only, Langfuse DB never; f1-micro no SLA; fixed host ports; no healthchecks on backend/litellm/kong/frontend; Kong rate-limit local + spoofable header, no auth; audit sink missing; backend public (allUsers), broad IAM, no WAF, no CORS; hardcoded NEXTAUTH secret; no LiteLLM timeout/budget/cache, shuffle routing; no deploy pipeline; no monitoring/alerting; CI lacks DB service and maybe dev tools; TF state shared across envs; Redis unused.
