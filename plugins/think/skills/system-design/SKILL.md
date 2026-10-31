---
name: system-design
description: Solution-architect checklist for scalable systems — requirements as numbers, capacity estimates, data and storage choice, consistency, partitioning, caching, async work, failure modes, security, observability, cost. Load when designing or reviewing any system or feature with scale, reliability or data concerns.
---

# System design checklist

Work through each section. Write "n/a" with a reason when one does not apply. Every claim about
how a technology behaves needs current docs (`think:docs-reader`), not memory.

## 1. Requirements as numbers
Functional scope (what is in, what is out). Then: daily and peak users, read/write QPS and the
ratio, payload sizes, data volume now and in 12 months, latency targets (p50/p99), availability
target (and the downtime it allows per month), RPO/RTO, consistency per operation, budget.

## 2. Back-of-envelope
QPS × payload = bandwidth. Records × size × replication = storage. Peak/average ratio. Working
set vs memory. Show the arithmetic so it can be checked.

## 3. Interfaces
The API surface and its contracts: idempotency keys for writes, pagination, versioning, rate
limits, error model. Sync vs async per call.

## 4. Data
Access patterns first, then the store. Relational (transactions, joins), key-value (point
lookups at scale), document, wide-column (write-heavy, time series), search index, object store,
graph. Schema, indexes, hot keys, and how the data grows.

## 5. Consistency and transactions
Per operation: strong, read-your-writes, eventual. Where you need cross-service consistency, name
the mechanism (single DB transaction, outbox, saga, idempotent consumers). Avoid distributed
transactions unless the evidence justifies them.

## 6. Scale
Stateless services behind a load balancer. Partitioning (key, range, hash; resharding plan).
Replication (leader/follower, multi-leader, leaderless; failover). Caching (what, where, TTL,
invalidation, stampede protection). Queues and streams for async work, back-pressure, retries
with jitter, dead-letter handling.

## 7. Failure modes
For each dependency: what happens when it is slow, down, or returns bad data. Timeouts, circuit
breakers, bulkheads, graceful degradation. Single points of failure. Behavior at 10x load.
Data loss scenarios and recovery.

## 8. Security and privacy
AuthN/AuthZ model, least privilege, secrets handling, encryption in transit and at rest,
input validation, multi-tenant isolation, PII and retention, audit trail.

## 9. Observability and operations
SLIs and SLOs tied to section 1. Metrics, logs, traces, alerts that page on symptoms. Deploys
(rollouts, rollbacks, migrations without downtime). Runbooks for the top failure modes.

## 10. Cost and team
Main cost drivers and how they scale. Managed vs self-run. What the team can operate.

## 11. Tradeoffs
What this design is good at, what it is bad at, and what it makes harder later.
