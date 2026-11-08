---
key: "E12-T2"
title: "Spike: BigQuery time-travel probe and observable windows"
epic: "E12"
repo: "FinAdvisor"
size: "S"
status: "todo"
depends_on: []
arch_refs: ["decision-logs.md#adr-30", "decision-logs.md#adr-29", "deep-dive/05-1-rls-indexes-versioning-and-deletion.md#5.14"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 297, "id": 6263777625, "url": "https://github.com/Keshav0375/FinAdvisor/issues/297"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Prove with a probe test that only the 2-day time-travel window is observable and the 7-day fail-safe is not.

## Description
ADR-030 'Proved by': a BigQuery probe test that proves only the 2-day time-travel window closed; fail-safe is not queryable (https://docs.cloud.google.com/bigquery/docs/time-travel). In a scratch dataset create a table with `max_time_travel_hours = 48`, insert a row, delete it, and query it with `FOR SYSTEM_TIME AS OF` before and after the window using a dataset configured with the minimum 48 h (use `max_time_travel_hours` 48 and a recorded wait, or a dataset with the lowest allowed value to shorten the run; state which). Record that a time-travel query at a timestamp older than the window fails, and that no documented query reads fail-safe data. Also confirm `ALTER PROJECT ... SET OPTIONS (default_max_time_travel_hours = 48)` per region and that a new dataset created without options inherits 48 (https://docs.cloud.google.com/bigquery/docs/default-configuration). Output `docs/adr/bigquery-erasure-probe.md` and a reusable probe function `bq_time_travel_probe(table, ts)` returning `closed` or `open`, used later by erasure-verify. Out of scope: the erasure DML itself.

## Acceptance criteria
- [ ] Given a deleted row inside the window, when `bq_time_travel_probe` runs at a timestamp inside the window, then it returns `open`; at a timestamp older than the window it returns `closed` (integration test against a scratch dataset).
- [ ] Given a dataset created with no options after `ALTER PROJECT` default 48, then its `max_time_travel_hours` reads 48 (INFORMATION_SCHEMA.SCHEMATA_OPTIONS query).
- [ ] `docs/adr/bigquery-erasure-probe.md` states that the fail-safe is not observable and marks the BigQuery 7 d fail-safe as `documented` in the receipt vocabulary.
