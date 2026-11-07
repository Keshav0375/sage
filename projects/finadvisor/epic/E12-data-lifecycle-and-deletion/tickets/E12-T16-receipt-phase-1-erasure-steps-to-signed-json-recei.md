---
key: "E12-T16"
title: "Receipt phase 1: erasure_steps to signed JSON receipt"
epic: "E12"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E12-T5", "E12-T7"]
arch_refs: ["deep-dive/06-interfaces-and-contracts.md#6.9", "deep-dive/04-2-source-lifecycle-and-cells.md#4.19", "decision-logs.md#adr-30", "deep-dive/09-observability.md#9.8"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 293, "id": 6263769348, "url": "https://github.com/Keshav0375/FinAdvisor/issues/293"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Issue the phase-1 'executed' receipt once, as the 6.9 JSON, stored in GCS and hashed in the ledger.

## Description
When every step is `done` or waiting on a window, build the receipt JSON of deep-dive/06 6.9 from `erasure_steps` (the envelope field names shown there, with `phase` 1, `windows_closed_at` null, `retained` for legal hold, `ledger_hash`). `subject_ref_hash` is the salted sha256, never the id. Sign the canonical JSON with the Cloud KMS HMAC key (`MAC` sign; key id in `signature.key_id`); write it to GCS, record `gcs_uri`, `hmac` and `issued_at` in `erasure_receipts` (idempotent on `(tenant_id, request_id, phase)`, so one receipt per request even after retries), and store the receipt's sha256 in the ledger row. The text of a phase-1 receipt never says 'erased everywhere'. Emit `erasure_receipts_open` (requests waiting for phase 2). Out of scope: phase 2 (E12-T17), the promise document.

## Acceptance criteria
- [ ] Given all steps done, when the issuer runs twice (including after a simulated crash between the GCS write and the DB insert), then exactly one phase-1 receipt row and one GCS object exist.
- [ ] Given a receipt, when the HMAC is recomputed with the KMS verify call over the stored JSON, then it matches; flipping one byte makes verify fail.
- [ ] Given a phase-1 receipt, then a string search finds no 'erased everywhere' and `windows_closed_at` is null (unit test on the builder).
- [ ] Given a legal-hold record, then the receipt `retained` array holds it with the legal basis text 'retained: legal basis X'.
- [ ] Given the receipt JSON, then it contains no document id, advisor id, text or email (leak test over the serialized receipt).
