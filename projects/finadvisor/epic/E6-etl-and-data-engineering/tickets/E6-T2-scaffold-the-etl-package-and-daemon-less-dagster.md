---
key: "E6-T2"
title: "Scaffold the ETL package and daemon-less Dagster"
epic: "E6"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E1-T3"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.8", "deep-dive/11-tech-stack.md#orchestration", "decision-logs.md#adr-014"]
issue: null
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Create the etl package with a Dagster definitions module that materializes in a Cloud Run job and runs locally with dagster dev.

## Description
Arch (4.8, `etl` job): 'Daemon-less: `dagster asset materialize` in a Cloud Run job; run and event storage in Postgres (`dagster-postgres`, database `dagster` on the same Cloud SQL instance, owned by role `fa_dagster`, no access to app schemas); `dagster dev` locally.' Build: package `backend/src/etl/` with `definitions.py` (Dagster `Definitions`), `dagster.yaml` selecting `dagster-postgres` storage from config `DAGSTER_PG_DB`, `DAGSTER_PG_USER`, `DAGSTER_PG_PASSWORD` (defaults `dagster`, `fa_dagster`), a `jobs` entrypoint subcommand `etl` that runs `dagster asset materialize --select <assets> --partition <tenant|dt>`, and a multi-dimensional partition def (tenant x date). Pin dagster, dagster-postgres, docling, pandera, presidio versions in pyproject. Local: `dagster dev` uses SQLite/in-memory run storage from a dev config. Out of scope: any real asset logic (later tickets), the Cloud Run job resource and Scheduler (infra epic).

## Acceptance criteria
- [ ] Given a Postgres with the `dagster` database from E1-T3, when `jobs etl --select noop_asset --partition tenant=a|dt=2026-01-01` runs, then the run record exists in the `dagster` DB and exit code is 0 (integration test)
- [ ] Given role `fa_dagster`, when it queries any app-schema table, then permission is denied (test)
- [ ] `dagster dev` starts locally with `docker compose` Postgres absent (smoke test with the dev config)
- [ ] No dagster-daemon or sensor process is required: `grep -r 'dagster-daemon' backend/ terraform/` returns nothing
