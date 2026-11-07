---
key: "E5-T9"
title: "Worker entrypoint with WORKER_ROLES dispatch"
epic: "E5"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E5-T8"]
arch_refs: ["deep-dive/04-components-and-responsibilities.md#4.7", "deep-dive/06-interfaces-and-contracts.md#6.6"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 86, "id": 6155671505, "url": "https://github.com/Keshav0375/FinAdvisor/issues/86"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Add the worker entrypoint that starts the roles named in WORKER_ROLES.

## Description
deep-dive/04-components-and-responsibilities.md#4.7: one image, entrypoint `worker`, roles selected by `WORKER_ROLES` (comma list of outbox-relay, silver, contextualizer, indexer, acl-applier, eval-judge, bq-sink), DB login role `fa_worker`. Implement the dispatcher in backend/src/worker/: parse and validate WORKER_ROLES (unknown role fails boot), run each role in its own task with graceful SIGTERM shutdown (finish the in-flight message, flush, commit), expose a role registry that E5-T10/E5-T11 and later epics plug into. Only outbox-relay and acl-applier are implemented in E5; the other roles register as 'not implemented' and fail boot with a clear error if selected. Out of scope: the roles themselves, Cloud Run config (E10).

## Acceptance criteria
- [ ] Given WORKER_ROLES=`bogus`, when the worker boots, then it exits non-zero with a message naming `bogus` (unit test).
- [ ] Given WORKER_ROLES=`outbox-relay,acl-applier`, when the worker boots, then both role tasks are running (test with stub roles).
- [ ] Given a running stub role, when SIGTERM is sent, then the role's shutdown hook runs and the process exits 0 within 10 s (test).
- [ ] Given WORKER_ROLES=`silver` in E5, when the worker boots, then it exits non-zero with 'role not implemented'.
