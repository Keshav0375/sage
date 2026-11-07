---
key: "E5-T3"
title: "Local compose: Kafka KRaft and Schema Registry"
epic: "E5"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: ["E5-T2"]
arch_refs: ["deep-dive/11-tech-stack.md", "deep-dive/06-interfaces-and-contracts.md#6.4", "deep-dive/06-interfaces-and-contracts.md#6.6", "decision-logs.md#adr-013"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 80, "id": 6155664798, "url": "https://github.com/Keshav0375/FinAdvisor/issues/80"}
branch: null
pr: null
updated: "2026-11-01"
---

## Summary
Add apache/kafka:4.4.0 and cp-schema-registry to docker compose with the topics created at startup.

## Description
deep-dive/11-tech-stack.md: local streaming is Apache Kafka KRaft single node `apache/kafka:4.4.0` plus Confluent cp-schema-registry (pin the tag in the compose file; deep-dive/11-tech-stack.md says 'pin at implementation'). Add both services to docker-compose.yml with env-driven host ports (ADR-019), health checks, and an init step (script or one-shot service) that creates the 11 topics of deep-dive/06-interfaces-and-contracts.md#6.4 with the partitions and retention from the E5-T2 ADR. Add settings KAFKA_BOOTSTRAP, KAFKA_API_KEY, KAFKA_API_SECRET, SCHEMA_REGISTRY_URL, SCHEMA_REGISTRY_API_KEY, SCHEMA_REGISTRY_API_SECRET to the pydantic-settings Settings class (deep-dive/06-interfaces-and-contracts.md#6.6; required, no secret default; local .env values are placeholders, local broker is PLAINTEXT). Out of scope: Confluent Cloud, producers, consumers.

## Acceptance criteria
- [ ] Given `docker compose up -d kafka schema-registry kafka-init`, when `kafka-topics.sh --list` runs in the broker, then exactly the 11 catalogue topics exist with the partition counts from the E5-T2 ADR.
- [ ] Given the stack is up, when `curl $SCHEMA_REGISTRY_URL/subjects` runs, then it returns HTTP 200 and `[]`.
- [ ] Given Settings is loaded with KAFKA_BOOTSTRAP unset, when the app boots, then it fails with a validation error naming KAFKA_BOOTSTRAP (unit test).
- [ ] Given the pinned image tags, when `docker compose config` runs, then the Kafka image is `apache/kafka:4.4.0` and no image uses `latest`.
