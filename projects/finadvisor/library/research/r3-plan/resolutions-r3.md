# Planning resolutions (round 3, ticket questions)

Orchestrator answers to the ticket-writer questions, 2026-11-01. Each answer follows the arch, or picks the
simplest default the arch allows. These become ADR-025 "Planning resolutions". Items marked KESHAV need
accounts or money from Keshav; they do not change the design.

## Cross-cutting
- R1 Spike ADRs. A spike ticket writes `docs/adr/<topic>.md` in FinAdvisor with measurements and the
  fallback taken. After merge, the researcher copies it into `arch/decisions.md` as the next ADR number.
  (E0.Q2, E1.Q1, E2.Q1, E3.Q2)
- R2 Migrations. E0-T9 creates revision 0001 = MVP schema.sql, immutable. E1 adds 0002+ that drop and
  recreate the MVP content tables with no data migration (never deployed; no data to keep). (E0.Q9, E1.Q4)
- R3 Table ownership. E1 creates every table in overview §5.2, including `answer_cache`, `turn_events`
  (with `request_hash`), `escalations`, the `halfvec(1024)` and `tsv` columns. E3-T4 adds only the HNSW and
  GIN indexes and the iterative-scan settings. E3-T13 adds only the `AnswerCache` class. (E3.Q1, E4.Q1)
- R4 Cloud provisioning. Local and CI bootstrap is E1-T3. Cloud SQL roles, passwords, the `dagster`
  database, Cloud Run jobs (`migrate`, `etl`, `etl-public`, `dbt`, `maintenance`, `eval`) and Cloud Scheduler
  are E10. VPC, Private Google Access, the private `run.app` zone, fa-gateway, ALB, Cloud Armor and the log
  sink are E2 (`terraform/edge/`); E10 reuses them. The SPA bucket is E10; E2-T8 takes it as a variable.
  BigQuery datasets, tables, authorized views and row policies are repo-managed idempotent DDL in E6-T17.
  (E1.Q5, E1.Q12, E2.Q3, E2.Q4, E6.Q1, E6.Q4, E7.Q6)
- R5 Weekly eval runs from a GitHub Actions cron (E7-T13). No Cloud Scheduler for evals. (E7.Q6)

## E0
- R6 Model lifecycle check: an allowlist in config of known model ids with retirement dates. Unknown ids
  fail. A model fails when retired or retiring within 30 days (`MODEL_RETIRE_WARN_DAYS`, default 30).
  A deprecated model with no retirement date passes with a warning. (E0.Q3)
- R7 Add `DB_PORT` (default 5432) to §6.6. (E0.Q4)
- R8 E0-T10 adds vitest and the dev image to the current Next.js app; E8-T1 replaces it with Vite. Accepted
  throwaway. (E0.Q5)
- R9 E0 compose holds postgres, kafka, migrate, api, frontend. Kong + Valkey come in E2-T11, Schema
  Registry in E5-T3, worker in E5-T9. Remove the self-hosted Langfuse compose and Redis. (E0.Q6, E0.Q7)
- R10 Remove the root Poetry project; `backend/poetry.lock` is the one lockfile (G-28). (E0.Q8)
- R11 Historical MVP docs stay as history under an allowlist; `.claude/settings.local.json` is untracked and
  removed from git. (E0.Q10)
- R12 Removing the MVP Kong service from Terraform in E0-T7 is intended; E2 adds the target gateway. (E0.Q11)
- R13 E0-T13 deletes eval-gate.yml; E7-T11 adds the new gate. (E0.Q12)
- R14 Branch protection required checks: manual step for Keshav after E0-T14, listed in its acceptance
  criteria as a `gh api` check that the builder can only report. (E0.Q13)
- R15 `JWT_SECRET` stays required with no default until E1-T15 removes it. `EMBED_MODEL` / `EMBED_DIM`
  belong to E3-T3. (E0.Q14, E0.Q15)

## E1
- R16 Planner-cost pass line for the partition spike: planning time p95 <= 10 ms at 52 partitions, and the
  ADR-003 trigger (ANN p95 <= 100 ms). (E1.Q3)
- R17 Neutral `app.*` values for principal load: nil uuid, empty role, tier `0`, empty jurisdictions.
  With these values RLS returns no content rows. (E1.Q6)
- R18 First advisors come from a seed command `migrate --seed-advisors <file>` in E1-T11, used by demo
  setup. No auto-provision on first login. (E1.Q7)
- R19 Entitlement cache: TTL-only, 60 s (ADR-002, ADR-004 win). Fix the ADR-010 text. (E1.Q8)
- R20 `MESSAGES_RETENTION_MONTHS` default 6. (E1.Q9)
- R21 DEFAULT-partition alert for `chunks` and `messages` is E9 (log-based metric + alert). (E1.Q10)
- R22 `fa_tenant_lookup(NULL, NULL)` returns no rows. Discovery never resolves the PUBLIC tenant (404).
  (E1.Q11)
- R23 Auth tests: Firebase Auth emulator in CI if the E1-T1 spike shows it supports multi-tenancy;
  else locally signed test JWTs with a test JWKS. E1-T1 records which. (E1.Q13)

## E2
- R24 X-RL-Key fallback: if `pre-function` cannot run before `rate-limiting`, limit by IP only and rely on
  the chat-api per-tenant budget; record it in the spike ADR. (E2.Q2)
- R25 The 50 ms SSE budget compares ALB+Kong against ALB direct to a test route on chat-api. (E2.Q5)
- R26 Rate limits (from 10 QPS peak, ~300 advisors): `RATE_LIMIT_IP_PER_MIN` 300 on all routes;
  `RATE_LIMIT_TOKEN_PER_MIN` 120 on api routes; `RATE_LIMIT_CHAT_PER_MIN` 20 per session on chat routes.
  Valkey down: fail open (`fault_tolerant: true`); chat-api budgets still apply. (E2.Q6)
- R27 `INPUT_MAX_CHARS` 4000; Kong request-size limit 64 KB until E4 and after. (E2.Q7, E4)
- R28 Client IP hash: HMAC-SHA256 with a secret salt from Secret Manager (`AUDIT_IP_SALT`). (E2.Q8)
- R29 `pre-function`: metadata server failure returns 503 (fail closed). Missing `Authorization` on
  chat/api routes returns 401 at Kong. (E2.Q9)
- R30 Strip client identity headers on all routes, including tenant-discovery. (E2.Q10)
- R31 Cloud Armor: no geo allow-list (demo users travel); throttle 600 req/min per IP; OWASP CRS
  preconfigured rules `sqli-v33-stable`, `xss-v33-stable` in preview first. Cost pass: <= $10/month idle.
  (E2.Q11)
- R32 E2-T21 cloud acceptance uses the E10 demo-up Valkey; move E2-T21 to depend on E10's demo-up ticket.
  Pin Valkey 8.0 (Memorystore) and `valkey/valkey:8.0` locally. (E2.Q12)
- R33 nginx error log: set `error_log` level to `crit` on proxied routes, and the T15 test proves no query
  string reaches Cloud Logging. (E2.Q13)
- R34 Two Kong services, same upstream: chat routes with `read_timeout` 3,600,000 ms; others default. (E2.Q14)
- R35 The Kong-ID-token check runs against the stub in E2; E10 re-runs it against the real chat-api. (E2.Q15)

## E3
- R36 Other rerank errors (5xx, network, bad response) fall back like a timeout with reason `error`.
  `embed_query`: 2 retries with jitter, then the turn fails with `RETRIEVAL_UNAVAILABLE`. (E3.Q3)
- R37 Degraded gate: pass if RRF returns at least `GATE_MIN_RESULTS` (default 2) candidates; the answer is
  marked `retrieval_degraded`. (E3.Q4)
- R38 E3-T16 sets the initial `GATE_MIN_SCORE`; E7-T7 sets the final value. (E3.Q5)
- R39 `STALE_AFTER_MONTHS` default 12, one key for retrieval, gold models and UI. (E3.Q6, E6.Q6)
- R40 `SEARCH_TOP_K_MAX` 10 and `RETRIEVAL_LEG_LIMIT` 40 become §6.6 keys. (E3.Q7)
- R41 E4 owns verifier and cache wiring in the orchestrator; E5-T11 (acl-applier) and E1-T12 (maintenance)
  own purge call sites. (E3.Q8)
- R42 PUBLIC changes rely on the PUBLIC `corpus_version` in the cache key; no cross-tenant purge. (E3.Q9)
- R43 `FACTSHEET_MAX_CHUNKS` default 8; E4 can change it. (E3.Q10, E4)
- R44 import-linter names the chat-api source roots; worker and job code stay outside. (E3.Q11)
- R45 Seeded synthetic vectors are fine for ANN latency; recall is measured in E7 with real embeddings. (E3.Q12)

## E4
- R46 Citation verifier on rejection: strip the unverified `[n]` marker, keep the sentence, count
  `citation_rejected_total`. If no verified citation is left in an answer that needs one, the turn becomes a
  refusal. Overlap threshold `CITATION_MIN_OVERLAP` default 0.5, tuned by E7. (E4.Q2)
- R47 Tenant token budget: daily window (UTC), counters in Postgres `tenant_usage` (no Valkey dependency in
  chat-api), `TENANT_TOKEN_BUDGET` default 2,000,000 tokens/day, `TENANT_MAX_CONCURRENCY` 20. (E4.Q3)
- R48 `turn_id` = UUIDv5(tenant_id, Idempotency-Key). Deltas batch every 250 ms or 512 chars. (E4.Q4)
- R49 Resume tails by polling `turn_events` every 250 ms. After `SSE_REPLAY_TTL_S` (default 600) resume
  returns 410 `TURN_EXPIRED`. (E4.Q5)
- R50 Presidio pseudonyms stay redacted in output; no re-identification. (E4.Q6)
- R51 MVP `litellm/` directory removal is E0-T6. (E4.Q7)

## E5
- R52 E5 defines minimal payload models; E4, E6, E7 add fields when they produce the event. (E5.Q1)
- R53 Keys: `KAFKA_CONSUMER_MAX_ATTEMPTS` 5, `KAFKA_RETRY_BACKOFF_MS` 500, `OUTBOX_RELAY_BATCH` 100,
  `OUTBOX_RELAY_POLL_MS` 500; add to §6.6. (E5.Q2)
- R54 E4-T21 owns the outbox insert helper; E5-T12 depends on it. (E5.Q3)
- R55 Metrics conventions module is E9; E5 emits `outbox_unpublished` as an OTel gauge now. (E5.Q4)
- R56 One `oneOf` schema per topic under `<topic>-value`; `dlq.v1-value` registered. (E5.Q5, E5.Q6)
- R57 Gap: no ticket builds the `bq-sink` worker role. Add it to E5. (E6.Q3)

## E6
- R58 Pipeline payloads: E5 envelope + id-only payloads. (E6.Q2)
- R59 Pandera: a failed chunk is rejected alone; a document with > 20% failed chunks is rejected whole. (E6.Q5)
- R60 Synthetic corpus: 60 documents per tenant, 3 tenants; 10k-chunk set for benchmarks. (E6.Q7)
- R61 E6 depends on E5 tickets E5-T7 (consumer framework), E5-T9 (worker entrypoint), E5-T11
  (acl-applier, which updates the denormalised ACL columns). (E6.Q9, E6.Q10)

## E7
- R62 E7-T16 owns the `eval.sample.v1` outbox row; E4 owns the feedback endpoint. (E7.Q1)
- R63 Judge acceptance: Cohen's kappa >= 0.6 against human labels. (E7.Q2)
- R64 PR gate uses the point estimate; the weekly full run uses the CI lower bound. (E7.Q3)
- R65 Baselines live in `data/eval/` in the repo. (E7.Q4)

## E8
- R66 Playwright runs against a stubbed API and the Firebase Auth emulator; one smoke spec runs against
  compose. (E8.Q1)
- R67 Firebase web config comes from `VITE_*` build env; E10 sets it in the deploy job. (E8.Q2)
- R68 `GET /v1/conversations/{id}/messages` returns `retrieval_degraded` and the caller's feedback score;
  E4 adds them. (E8.Q3)
- R69 `escalate_offer=true` shows a hint and an "Ask compliance" button that sends the follow-up turn. (E8.Q4)
- R70 SSE resume: 5 attempts, backoff 1, 2, 4, 8, 16 s. (E8.Q5)

## E9
- R71 Shared metrics module `backend/src/observability/metrics.py` is created by E9-T5. Earlier epics emit
  with plain OTel meters and E9-T5 moves them to the registry. (E9.Q1)
- R72 Alert numbers accepted: outbox oldest age > 300 s, ACL apply lag > 120 s, consumer lag > 1000 for
  10 min; availability burn rate 14.4x / 1 h and 6x / 6 h. (E9.Q2)
- R73 Add `llm_cost_usd_total{provider,model}` computed from token counts and a price table in config;
  the budget alert uses GCP billing plus this metric. (E9.Q3)
- R74 Add `readiness_failing` and `model_retirement_days` (gauge) to §9.2. (E9.Q4)
- R75 Notification channel: email to `alert_email`. (E9.Q5)
- R76 The maintenance job runs every 15 min in demo mode (E10 schedules it); the DEFAULT-partition alert
  window is 30 min. (E9.Q6, R21)
- R77 OTel export: direct OTLP to the Google Cloud Telemetry API endpoint with ADC, no sidecar. E9-T2 checks
  this first; fallback is an OTel Collector sidecar, recorded as a spike ADR. (E9.Q7)

## E10
- R78 Backups: demo profile daily automated backups, 7 retained, PITR off (RPO 24 h, RTO 1 h); prod
  profile PITR on, 7-day log retention (RPO 5 min, RTO 1 h). (E10.Q1)
- R79 A `db-bootstrap` Cloud Run job as `fa_owner` creates roles and writes passwords to Secret Manager
  versions; no passwords in Terraform state. (E10.Q2)
- R80 Scheduler pause state goes in `ignore_changes`. Crons (UTC): etl daily 02:00, etl-public weekly Mon
  03:00, dbt daily 04:00, redteam weekly Sun 05:00, maintenance every 15 min (R76); eval weekly is GitHub
  Actions (R5). Demo-down pauses all. (E10.Q3)
- R81 `DEMO_TTL_HOURS` 4. (E10.Q4)
- R82 Kong reads the Valkey endpoint from env `KONG_VALKEY_HOST` / `KONG_VALKEY_PORT` (E2-T11 sets the
  names); fa-gateway Terraform does not ignore them; demo-up applies them. (E10.Q5)
- R83 SPA bucket: uniform bucket-level access, `allUsers` with `roles/storage.legacyObjectReader` only
  (object read, no listing). Static assets only, no data; a recorded exception to "no allUsers on any
  service", which covers Cloud Run services. (E10.Q6)
- R84 Demo-down drain checks run inside a Cloud Run job. (E10.Q7)
- R85 Terraform apply and deploy use the GitHub environment `prod` with Keshav as required reviewer. (E10.Q8)

## KESHAV (accounts and money, not design)
- K1 A GCP project id with billing, Identity Platform multi-tenancy enabled (E1-T1, all cloud tickets).
- K2 Langfuse Cloud Hobby project keys, stored as GitHub secrets `LANGFUSE_PUBLIC_KEY`,
  `LANGFUSE_SECRET_KEY` and in local `.env` (E0-T1).
- K3 A domain for the ALB managed certificate (E2-T8, E10).
- K4 About 30 human labels for the judge spike: Keshav labels them with the CLI (E7-T1).
- K5 Enable branch protection on `main` after E0-T14 (R14).
