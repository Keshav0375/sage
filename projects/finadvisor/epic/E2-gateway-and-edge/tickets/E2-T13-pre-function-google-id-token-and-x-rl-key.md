---
key: "E2-T13"
title: "pre-function: Google ID token and X-RL-Key"
epic: "E2"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E2-T12", "E2-T7", "E2-T1"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.3", "deep-dive/06-interfaces-and-contracts.md#6.5", "deep-dive/08-security-and-privacy.md#8.2", "decision-logs.md#adr-011"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 51, "id": 6155631548, "url": "https://github.com/Keshav0375/FinAdvisor/issues/51"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Promote the spike logic into the production pre-function that sets X-Serverless-Authorization and X-RL-Key on every proxied route.

## Description
Sections 4.3, 6.5, 8.2 step 6 and ADR-011, using the E2-T1 and E2-T7 results (if either ADR chose a fallback, implement that fallback instead and say so). Quote 4.3: pre-function '(a) sets X-Serverless-Authorization: Bearer <Google ID token> (from the metadata server, audience = chat-api URL, cached until near expiry), leaving the user's Authorization intact, and (b) sets X-RL-Key = sha256(Authorization) so raw tokens never reach Valkey keys.' Keep the Lua in git (kong/lua/), unit-tested, and inlined into kong.yml by a documented build step that CI re-runs. Metadata host from GCE_METADATA_HOST (default metadata.google.internal) so compose points at the stub mock. The pre-function runs before rate-limiting in the access phase on chat, chat-resume and api (tenant-discovery has no bearer). Behaviour on metadata failure and on a missing Authorization follows question 9; until answered fail closed with 503 on metadata failure and record the choice.

## Acceptance criteria
- [ ] Given Lua unit tests (test_sha256_known_vector with the NIST vector for 'abc', test_token_cache_reuse, test_token_refresh_within_margin with an injected clock and fake metadata), then all pass in CI.
- [ ] Given compose and the metadata mock, when a request with Authorization: Bearer SENTINEL_BBB is sent to POST /v1/chat, then the stub sees X-Serverless-Authorization with the mock token (aud = CHAT_API_URL), an unchanged Authorization (equal sha256) and X-RL-Key equal to sha256 of the Authorization value.
- [ ] Given the metadata mock stopped, then the request returns 503 and the stub receives nothing; the chosen behaviour is stated in the PR.
- [ ] Given the order test from E2-T1 re-run on the final kong.yml, then X-RL-Key is set before rate-limiting evaluates (a burst by one token is limited, a different token is not).
