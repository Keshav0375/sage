---
key: "E2-T11"
title: "Compose: Kong 3.9.4, Valkey and the stub"
epic: "E2"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E2-T3", "E2-T1", "E0-T14"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.3", "deep-dive/04-components-and-responsibilities.md#4.6", "deep-dive/11-tech-stack.md"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 49, "id": 6155629138, "url": "https://github.com/Keshav0375/FinAdvisor/issues/49"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Run the gateway locally with Valkey and the stub, replacing the MVP LiteLLM-based Kong wiring.

## Description
Overview 4.3 'Local: kong:3.9.4 + Valkey in compose', 4.6 and deep-dive/11-tech-stack.md (Valkey 'pin at implementation'). Update docker-compose.yml: kong built from kong/Dockerfile (E2-T5), env-driven host port, admin listener off, status listener on its own port, healthcheck; a valkey service (pin the image tag by digest, record the version in the PR for deep-dive/11-tech-stack.md) with a healthcheck (valkey-cli ping); the E2-T3 stub as service `chat-api-stub` (profile gateway-test); remove the unused redis service and every LiteLLM reference from kong/ and compose. Kong env: VALKEY_HOST/PORT, CHAT_API_URL and the metadata mock host. Out of scope: other compose services (E0).

## Acceptance criteria
- [ ] Given `docker compose --profile gateway-test up -d kong valkey chat-api-stub`, then all three report healthy within 60 s.
- [ ] Given a request to the Kong proxy host port for an unknown path, then the response is HTTP 404 with Kong's JSON body; a connection to the admin port (8001) is refused.
- [ ] Given the repo, `grep -ril litellm kong docker-compose*.yml` returns nothing and `grep -n 'redis:7' docker-compose.yml` returns nothing (test script tests/gateway/test_no_legacy.sh).
- [ ] Given `docker compose config`, then it exits 0 with no fixed host-port collision when two checkouts use different port env values.
