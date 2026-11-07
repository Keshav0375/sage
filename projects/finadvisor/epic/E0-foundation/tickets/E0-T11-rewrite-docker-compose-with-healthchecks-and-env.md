---
key: "E0-T11"
title: "Rewrite docker compose with healthchecks and env-driven host ports"
epic: "E0"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E0-T2", "E0-T5", "E0-T6", "E0-T9", "E0-T10"]
arch_refs: ["deep-dive/01-context-and-goals.md#1", "deep-dive/04-components-and-responsibilities.md#4", "decision-logs.md#adr-019", "decision-logs.md#adr-021", "deep-dive/11-tech-stack.md#local-orchestration"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 12, "id": 6155582481, "url": "https://github.com/Keshav0375/FinAdvisor/issues/12"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
`docker compose up --wait` brings postgres, kafka, migrate, api and frontend healthy using the pinned pgvector image, with every host port overridable.

## Description
Why: G-49: the override file targets a missing stage, nothing has healthchecks, `kong` waits only for start, host ports are fixed, and a duplicate standalone Langfuse compose conflicts on ports. ADR-019: "Local dev = docker compose with the same image." ADR-021 / deep-dive/11-tech-stack.md: local and CI Postgres is `pgvector/pgvector:0.8.5-pg16` to match Cloud SQL; local Kafka is `apache/kafka:4.4.0` KRaft single node. G-25: no secret defaults.

Rewrite `docker-compose.yml` (and fix `docker-compose.override.yml`):
- `postgres`: `pgvector/pgvector:0.8.5-pg16`, credentials from `DB_NAME`, `DB_USER`, `DB_PASSWORD` (`${DB_PASSWORD:?set DB_PASSWORD in .env}`), named volume, `pg_isready` healthcheck; remove the `schema.sql` initdb mount (Alembic owns the schema).
- `kafka`: `apache/kafka:4.4.0` single-node KRaft, healthcheck using the bundled `kafka-broker-api-versions.sh`, an in-network listener for containers and a host listener whose advertised port equals `KAFKA_HOST_PORT`.
- `migrate`: same backend image, command `jobs migrate`, `depends_on: postgres: service_healthy`, `restart: "no"`.
- `api`: backend image (override uses the `dev` target with source mounts), `depends_on` migrate `service_completed_successfully`, healthcheck GET `/healthz` using Python's stdlib (slim image has no curl), env from Settings keys (`ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, `VOYAGE_API_KEY`, `JWT_SECRET`, `DB_*`, pool and timeout keys), all secrets required via `${VAR:?...}`.
- `frontend`: `frontend/Dockerfile` dev target from E0-T10, `depends_on: api: service_healthy`, healthcheck on `/`.
- Host ports bound to `127.0.0.1` and env-driven with defaults: `POSTGRES_HOST_PORT`, `KAFKA_HOST_PORT`, `API_HOST_PORT`, `FRONTEND_HOST_PORT`.
- Remove the unused `redis`, the self-hosted `langfuse` and `langfuse-db` services and delete `langfuse/docker-compose.langfuse.yml` (ADR-018 rejected self-hosting; Langfuse Cloud is used when `LANGFUSE_ENABLED=true`; see questions).
- Update `backend/src/cli.py` (`finadvisor` launcher): stop piping `schema.sql` into the removed initdb path; run the `migrate` service and use `docker compose up --wait`. Update `.env.example` with the host-port variables.

Out of scope: Kong, Valkey, Schema Registry and the `worker` service (E2 / E5 add them), Terraform.

## Acceptance criteria
- [ ] Given a valid `.env`, `docker compose up -d --wait` exits 0 and `docker compose ps --format json` shows `postgres`, `kafka`, `api` and `frontend` as `healthy` and `migrate` as `exited (0)`.
- [ ] Given a stray listener on 5432, 8000, 3000 and 9092 (for example `python -m http.server` on each) and `POSTGRES_HOST_PORT=15432 API_HOST_PORT=18000 FRONTEND_HOST_PORT=13000 KAFKA_HOST_PORT=19092`, `docker compose up -d --wait` still exits 0 (no fixed host-port collision), and a second project (`-p other`) with different ports runs side by side.
- [ ] Given `DB_PASSWORD` unset, `docker compose config` exits non-zero with the `set DB_PASSWORD` message (no secret default).
- [ ] `docker compose config | grep -E "image:"` shows `pgvector/pgvector:0.8.5-pg16` and `apache/kafka:4.4.0` and no `redis`, `langfuse`, `litellm` or `kong` image.
- [ ] Given a clean DB volume, after `up --wait`, `docker compose exec postgres psql -U $DB_USER -d $DB_NAME -c "select version_num from alembic_version"` returns `0001`; `curl -fsS localhost:$API_HOST_PORT/healthz` returns 200 and `/readyz` returns 200.
- [ ] `docker compose down -v` leaves no containers or volumes for the project (`docker compose ps -a` empty).
