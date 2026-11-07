---
key: "E2-T1"
title: "Spike: X-RL-Key keying and Valkey keys on Kong 3.9.4"
epic: "E2"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: []
arch_refs: ["deep-dive/10-open-questions.md#10", "deep-dive/06-interfaces-and-contracts.md#6.5", "deep-dive/04-components-and-responsibilities.md#4.3", "decision-logs.md#adr-011"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 39, "id": 6155617124, "url": "https://github.com/Keshav0375/FinAdvisor/issues/39"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Prove locally that a pre-function can set X-RL-Key = sha256(Authorization) before rate-limiting runs and that raw bearer tokens never reach Valkey.

## Description
Overview section 10 item 5 and ADR-011. Scratch harness under spikes/e2/xrlkey/ (not shipped): kong:3.9.4 DB-less, a Valkey container, any HTTP upstream. Configure a pre-function (access phase) that sets request header X-RL-Key to the hex sha256 of the Authorization header, and rate-limiting with limit_by: header, header_name: X-RL-Key, policy: redis, sync_rate: 0 against Valkey, low limit (3/min). Quote from 6.5: 'The pre-function sets X-Serverless-Authorization and X-RL-Key = sha256(Authorization) (so raw tokens never become Valkey keys) and runs before rate-limiting in the access phase; verified in the E2 spike.' Determine and record: (a) plugin execution order (pre-function before rate-limiting) and how it is guaranteed; (b) whether sha256 is available inside the pre-function sandbox (which requires, any Kong sandbox setting needed); (c) what rate-limiting does when X-RL-Key is absent (the header is missing when a request has no Authorization); (d) that a client-sent X-RL-Key is overwritten. Out of scope: the production kong.yml, the metadata-server token logic.

## Acceptance criteria
- [ ] Given a 3 per minute limit, when 4 requests with the same Authorization are sent, then the 4th returns 429 with a Retry-After header and a request with a different Authorization returns 200 (script spikes/e2/xrlkey/run.sh output committed with the ADR).
- [ ] Given traffic from two bearer tokens, when every Valkey key and value is dumped (valkey-cli --scan plus GET/TTL), then the raw bearer strings occur 0 times (grep -c = 0) and the keys contain the 64-hex sha256 of each token.
- [ ] Given a request sending X-RL-Key: fixed with varying Authorization values, when it is repeated beyond the limit with different tokens, then each token keeps its own bucket (client value ignored).
- [ ] Given a request with no Authorization header, then the ADR records the observed behaviour (status, key used) measured by a test run, not assumed.
- [ ] ADR exists with plugin order, sandbox findings, the four measurements and a verdict. The result is recorded as an ADR file in the repo (see question 1 for location and numbering) containing the measured values, the pass/fail verdict and the named fallback. The arch gives no fail branch for this spike (question 2); on failure the ticket is marked blocked with the ADR instead of choosing one.
