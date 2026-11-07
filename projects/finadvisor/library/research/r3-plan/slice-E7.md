# Slice E7

## Epic section (from arch/plan.md)

### E7 Evaluation

- **Goal.** A measured, blocking quality bar for retrieval, answers, refusal and leaks.
- **Scope.**
  - Golden set from 50 to ~300 questions (tenant-parameterised, adversarial, refusal).
  - L1 retrieval eval with dense / FTS / hybrid / rerank ablation (also sets `RERANK_CANDIDATES`); L2 Ragas collections with a Haiku judge calibrated on ~30 human labels (Cohen's kappa) and CI bounds.
  - CI gate: ~60-question PR subset, weekly full run, run against the fallback model; promptfoo red team; `eval` and `redteam` jobs as `fa_eval` against the `eval` tenant.
  - L4 online judging: the `eval-judge` worker consumes `eval.sample.v1` (5-10% sample, `EVAL_SAMPLE_RATE`), writes scores to Langfuse and `eval_scores`; thumbs feedback to `eval.events.v1`.
- **Arch sections.** overview.md#4.14 (flow 4), overview.md#4.7 (`eval-judge`), overview.md#8.1, overview.md#9.6; ADR-017, ADR-016, ADR-008.
- **Dependencies.** E4, E6.
- **Spikes first.** Judge calibration (kappa on ~30 labels) before the L2 numbers are trusted.
- **Done when.**
  - The PR gate fails a deliberate regression in each of: citation < 0.95, faithfulness < 0.90, a planted cross-tenant leak, recall drop > 2 points (four test PRs).
  - The weekly full run executes with CI lower bounds reported; the fallback model run exists and gates `LLM_FALLBACK_ENABLED`.
  - The ablation report records the decision on rerank and contextual retrieval (kept or dropped, with recall and latency).
  - The `eval-judge` scores at least one sampled turn end to end into Langfuse and `eval_scores` (tenant RLS applies; `fa_app` has no access to the table).
  - Fixes G-06, G-54, G-56.

## Arch files to read (paths; read only the named subsections)

- context/projects/finadvisor/arch/overview/04-components-and-responsibilities.md  (sections: 4.14, 4.7)
- context/projects/finadvisor/arch/overview/08-security-and-privacy.md  (sections: 8.1)
- context/projects/finadvisor/arch/overview/09-observability.md  (sections: 9.6)
- context/projects/finadvisor/arch/stack.md (versions)
- context/projects/finadvisor/arch/overview/06-interfaces-and-contracts.md §6.6 (config keys), only the keys this epic uses

## ADRs (context/projects/finadvisor/arch/decisions.md; line of heading)

- line 348: ADR-008: Hybrid retrieval, rerank, confidence gate and chunking
- line 177: ADR-016: Contextual retrieval at ingest, behind a flag
- line 156: ADR-017: Evaluation strategy and deploy gate
