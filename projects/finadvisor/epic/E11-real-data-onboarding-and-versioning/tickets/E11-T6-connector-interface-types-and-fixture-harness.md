---
key: "E11-T6"
title: "Connector interface, types and fixture harness"
epic: "E11"
repo: "FinAdvisor"
size: "M"
status: "todo"
depends_on: ["E6-T2", "E11-T4"]
arch_refs: ["deep-dive/04-2-source-lifecycle-and-cells.md#4.15", "deep-dive/06-interfaces-and-contracts.md#6.7", "decision-logs.md#adr-26"]
issue: {"repo": "Keshav0375/FinAdvisor", "number": 282, "id": 6263739473, "url": "https://github.com/Keshav0375/FinAdvisor/issues/282"}
branch: null
pr: null
updated: "2026-11-07"
---

## Summary
Define the four-method Connector protocol, its types and the recorded-fixture (VCR) test harness.

## Description
Create `backend/src/connectors/base.py` and the fixture harness. Arch (6.7): the four methods are fixed by the decision.

```python
class Connector(Protocol):
    source_id: str
    source_class: Literal["law", "qa", "fca_api", "publisher"]
    def list(self) -> list[ListingItem]: ...
    def changes(self, cursor: dict) -> list[Observation]: ...
    def fetch(self, item: ListingItem) -> bytes: ...
    def classify(self, item: ListingItem) -> Classification: ...
```

Types as Pydantic models: `ListingItem(external_id, version_key, source_ts, locator)`, `Observation(source_id, external_id, version_key, content_sha256, source_ts, observed_at, state)`, `Classification(jurisdiction, tier, licence_class, language, authoritative, attribution_text, valid_from, valid_from_basis)`. `licence_class` is a closed enum: `us_gov`, `eu_consolidated_ccby`, `esma_transformed`, `ogl`, `ogl_fca`, `publisher`. Add a shared HTTP client with per-connector throttle (`rate_limit_rps` from `source_registry`), declared User-Agent and gzip support, and a recorded-fixture mode: connectors run against VCR cassettes in the PR gate and against live sources only in the weekly smoke (marker `live`).

Observation JSON Schemas are registered like other events (BACKWARD, CI check, ADR-013 via E5-T5).

Out of scope: any concrete connector; change capture logic (E11-T7, T8).

## Acceptance criteria
- [ ] Given a class that omits one of the four methods when it is checked with `isinstance`-style protocol test then registration fails (test `backend/tests/connectors/test_protocol.py::test_missing_method_rejected`).
- [ ] Given a `Classification` with a `licence_class` outside the enum or null `attribution_text` when validated then a ValidationError is raised (test `test_classification_validation`).
- [ ] Given a throttle of 1 rps when a fake connector makes 5 calls then the wall time is >= 4 s with a fake clock (test `test_throttle_respects_rps`).
- [ ] Given cassette mode when a test makes a request not in the cassette then it fails (no live network in PR; test `test_no_live_network_in_pr_gate`).
- [ ] The Observation JSON Schema is registered and a breaking change fails the CI schema check (test `test_observation_schema_backward_compatible`).
