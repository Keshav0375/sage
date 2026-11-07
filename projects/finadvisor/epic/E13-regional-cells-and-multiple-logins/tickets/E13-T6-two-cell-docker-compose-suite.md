---
key: "E13-T6"
title: "Two-cell docker compose suite with a cells.json router"
epic: "E13"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E13-T2", "E5-T3", "E2-T11", "E4-T14", "E6-T12"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.24", "deep-dive/07-scaling-failure-modes-and-recovery.md#7.6", "decision-logs.md#adr-031"]
issue: null
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
`docker-compose.cells.yml` runs two complete cells on separate networks plus a router that serves the signed `cells.json`.

## Description
Implements: "a second cell exists as a two-cell docker compose suite (`docker-compose.cells.yml`: networks `cell-us` and `cell-eu`, separate Postgres, Kafka, schema registry, a router container serving `cells.json`)" (04-2 §4.24). Only `us-central1` is deployed; the second cell is local only (K-R4-1, no real second region). RAM 4-6 GB is an ASSUMPTION (ADR-031) and is measured here.

Create `docker-compose.cells.yml`: per cell, on its own network (`cell-us`, `cell-eu`): Postgres+pgvector, Kafka (KRaft) and schema registry (from E5-T3), chat-api and worker (`HOME_CELL=us|eu`, `CELLS_JSON_URI` pointing at the router, `CELLS_PUBLIC_KEY` from the E13-T1 test keys), Kong (E2-T11). A `router` container on both networks serves the signed `cells.json` and routes per-cell hostnames to each cell's Kong. Seed one firm per cell (`alpha` in us, `beta` in eu, `residency_class: eu_only`) plus PUBLIC in each cell via the existing onboarding command. Make targets `make cells-up`, `cells-down`. Document the measured peak RAM in `docs/runbooks/cells-compose.md`; if above 6 GB, record it (do not change the arch).

Out of scope: separation assertions (E13-T8), cell-down behaviour (E13-T7), PUBLIC manifests (E13-T9), any cloud resources.

## Acceptance criteria
- [ ] Given `make cells-up`, when every healthcheck settles, then `curl` of the router's `/resolve?slug=alpha` returns cell `us` and `slug=beta` returns cell `eu` (`make test-cells-smoke`).
- [ ] Given the running suite, when a chat request is made for `alpha` on the us hostname and for `beta` on the eu hostname, then both succeed with the stub LLM (`test_cells_compose.py::test_each_cell_serves_own_tenant`).
- [ ] Given the suite, then `docker network inspect` shows the cell-us and cell-eu data services (Postgres, Kafka) attached to exactly one cell network each (`test_cells_compose.py::test_network_membership`).
- [ ] `docs/runbooks/cells-compose.md` records the measured peak RAM of the suite (checked by `make cells-ram` which fails if the file lacks the number).
