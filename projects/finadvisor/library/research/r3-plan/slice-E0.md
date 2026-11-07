# Slice E0

## Epic section (from arch/plan.md)

### E0 Foundation

- **Goal.** The repo is runnable and honest: it builds from lockfiles, boots only with real config, and CI can fail.
- **Scope.**
  - Single typed `Settings` (pydantic-settings), no secret defaults (fail to boot); model ids from config plus a retired-model check (CI and readiness).
  - Remove LiteLLM and the Kong/LiteLLM wiring; Langfuse Python SDK 5.x wrapper (`mask_otel_spans`, capture off on sensitive spans).
  - CI with lockfile installs, Postgres and Kafka service containers (`pgvector/pgvector:0.8.5-pg16` to match Cloud SQL); ruff, mypy, pytest, eslint, tsc, vitest, trivy, gitleaks, pip-audit.
  - docker compose with env-driven host ports, healthchecks, the same pgvector image, and a frontend dev image.
  - Alembic baseline created from `schema.sql`; `migrate` entrypoint.
- **Arch sections.** overview.md#1 (gap map), overview.md#6.6 (config keys), overview.md#4 (compute shape); ADR-005, ADR-006, ADR-018, ADR-019, ADR-021.
- **Dependencies.** none.
- **Spikes first.** none (confirm Langfuse Cloud accepts SDK 5.x as the first ticket).
- **Done when.**
  - CI is green on a clean clone using lockfiles only, and each of ruff, mypy, pytest, eslint, tsc, vitest, trivy, gitleaks, pip-audit runs and can fail a PR.
  - Starting the app with a missing required secret exits non-zero (test).
  - `claude-sonnet-4-20250514` in config makes CI and `/readyz` fail (test); the repo contains no LiteLLM service, config or dependency.
  - `docker compose up` brings every service healthy with no fixed host-port collisions; Alembic upgrade on an empty database equals the baseline schema.
  - Fixes G-05, G-08, G-09 (removal), G-15, G-25, G-28, G-49.

## Arch files to read (paths; read only the named subsections)

- context/projects/finadvisor/arch/overview/01-context-and-goals.md  (sections: 1)
- context/projects/finadvisor/arch/overview/04-components-and-responsibilities.md  (sections: 4)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md  (sections: 6.6)
- context/projects/finadvisor/arch/stack.md (versions)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md §6.6 (config keys), only the keys this epic uses

## ADRs (context/projects/finadvisor/arch/decisions.md; line of heading)

- line 413: ADR-005: Drop LiteLLM; in-process LLMClient with same-provider fallback
- line 392: ADR-006: Models and prompt caching
- line 134: ADR-018: Observability and Langfuse Cloud
- line 112: ADR-019: Compute mapping: one image, three entrypoints, Cloud Run, Vite SPA
- line 69: ADR-021: CI/CD with GitHub Actions, WIF and a gated deploy
