# Round 4 stage-1 checkpoint: Keshav's answers (2026-11-02)

Binding inputs for stage 2 (design). Evidence: evidence-r4.md (merged, skeptic-corrected).

- K-R4-1 Regions: keep D-R4-1. Two regional cells designed and tested locally in docker compose;
  one region deployed. Residency covers data at rest (Postgres, GCS, BigQuery, Kafka, Langfuse).
  Model calls are documented as US/global (Anthropic first-party has inference_geo global|us only).
  Claude on Vertex AI in an EU region stays a costed option in the ADR, not built.
- K-R4-2 UK source: current FCA COBS from the FCA Handbook API (handle revocation and
  delete-on-request), UK version history from legislation.gov.uk (OGL). No crawling of the
  Handbook website. FINRA Rulebook dropped (terms forbid bulk copy and ML use).
- K-R4-3 Publisher documents (fund KIDs, SEC 497K, Form ADV brochures): private demo only. Fetch a
  small set (about 3 fund families, 10-20 brochures) at runtime into private storage, with
  attribution. Never commit them to the public repo or publish them in eval sets.
- K-R4-4 Golden set: 200 items labelled by Keshav (about 40-55 h estimate). Release gates and
  ablations with gains of about 5 points or more; stays above 100 effective items after
  clustering by source document.
