# Track D - guardrail tools (r4) - EVIDENCE
Read 2026-11-02. Leaf extracts (quotes live there): pages/D-model-armor.md, D-classifiers.md, D-presidio-nemo.md, D-anthropic-spotlighting.md.
Caveat: quotes below were taken from the leaf hand-backs; the Presidio/NeMo ones came via WebFetch summaries (not raw page text). Check against the extract files before any decision uses them.

## 1. Google Cloud Model Armor
Confirms
- Free tier then $0.10/1M tokens, SDP adds no charge - "no cost ... up to 2 million tokens per month ... $0.10 per million tokens" - cloud.google.com/security-command-center/pricing (no date, read 2026-11-02). Matches ADR-009.
- Detect-only REST API, caller enforces - modes Inspect-only and Inspect-and-block; caller applies the block - docs.cloud.google.com/model-armor sanitize page (2026-11-02). Overview says it covers "other cloud providers" (works with Anthropic API).
- Filters: PI + jailbreak, malicious URL (first 256 URLs only), SDP PII, RAI (hate, harassment, sexual, dangerous), CSAM "applied by default and cannot be turned off" - overview (2026-10-26).
- Document screening: PDF, CSV, TXT, DOCX/DOCM, PPTX, XLSX; "Supported files are limited to 4 MB in size" - overview/document screening. Fit for ingest-time (b), but 4 MB cap; images Preview.
Limits
- "1200 queries per minute (QPM) per project" - quotas (2026-10-28). Token limits 65,536 (PI/jailbreak, RAI, CSAM), 130,000 (SDP). Over limit the filter returns EXECUTION_SKIPPED (caller must treat as fail-closed or not). 16 regions + us/eu multi-regions (locations page, undated).
- Confidence levels HIGH / Medium and above / Low and above apply to PI and RAI only; SDP uses match likelihood.
- Languages: RAI and PI tested on 9 languages; SDP depends on infoTypes.
- Ingest at scale: 1200 QPM caps bulk chunk scanning; batch documents (not chunks) or throttle.
Gaps
- Latency: NOT FOUND (only qualitative "low-latency"). SLA: NOT FOUND. GA/Preview per feature: NOT FOUND (images and exclusion rules are Preview). Published precision/recall: NOT FOUND. => the 500 ms fail-closed timeout in ADR-009 is unsupported by vendor numbers; must be measured.
- SDP Basic = 6 US-centric infoTypes, inspection only. Advanced uses inspect + de-identify templates; de-identify not supported for file prompts or streaming. So Model Armor cannot be the pseudonymizer; Presidio stays.
- Some doc URLs (pricing, filters-overview, templates-overview) returned 404 - doc layout moving.

## 2. Microsoft Presidio
- Version/licence - PyPI presidio-analyzer 2.2.366 uploaded 2026-10-27, MIT, Python >=3.11,<3.15. Docs now at presidio.dataprivacystack.org. ADR-009 "2.2.x" still current.
- NLP: default spaCy model, optional transformers; default config English only (multi-language needs per-language recognizers/models).
- Anonymizer operators: replace, redact, mask, hash, encrypt, custom, keep; deanonymize only for encrypt (decrypt). Reversible pseudonymization needs app-side mapping or encrypt operator.
- Gaps: latency NOT FOUND; published recall/precision NOT FOUND. README: vanilla results "aren't very accurate" (leaf quote). => E4 benchmark in ADR-009 is mandatory; nothing in docs backs a recall number.
- Fit: (a) yes, in-process; (b) yes at ingest, CPU only, no per-token cost; (c) yes (sentence-buffered). Not an injection detector.

## 3. NVIDIA NeMo Guardrails
- Version 0.24.1 (PyPI 2026-09-16), Apache-2.0, Python >=3.10,<3.14. 5 rail types (input, dialog, retrieval, execution, output).
- Built-ins: self-check (LLM), jailbreak heuristics (gpt2-large perplexity; docs "2057 ms CPU and 115 ms GPU via Docker", fails open), Presidio PII (needs en_core_web_lg, default threshold 0.2), content safety (Nemotron, Llama Guard 3, ShieldGemma), fact-check/hallucination (LLM-based).
- Fact-check/hallucination/jailbreak-heuristic rails run only on LLMRails, not IORails.
- Gaps: general overhead figure NOT FOUND; injection-detection behaviour NOT FOUND (stub page).
- Contradicts nothing in ADR-009 (rejected for latency); the only vendor-stated figure (2057 ms CPU) supports rejecting its jailbreak rail on CPU Cloud Run. Possible use: library of heuristics only - not recommended.

## 4. Open classifiers (D-classifiers.md)
- Prompt Guard 2 (Meta MODEL_CARD): latency "(A100 GPU, 512 tokens)" 92.4 ms (86M), 19.3 ms (22M); AUC English .998 / .995; recall @1% FPR 97.5% / 88.7%; context 512 tokens; binary benign/malicious, covers injection + jailbreak. Licence shown as "other" (Llama terms; terms text not on page: UNVERIFIED). GPU latency only; CPU latency NOT FOUND. 512-token window forces chunk windowing for documents.
- protectai/deberta-v3-base-prompt-injection-v2: Apache-2.0, English only, archived, does not detect jailbreaks, 91.59% precision / 99.74% recall on 20k prompts. Archived => maintenance risk.
- IBM Granite Guardian 4.1-8b: Apache-2.0, 8B (needs GPU); newer granitelib-guardian-r1.0 LoRA library dated 2026-10-16. Too heavy for hot path on Cloud Run CPU.
- Qwen3Guard-Gen-0.6B: Apache-2.0, 119 languages, categories include Jailbreak and PII; generative classifier (latency NOT FOUND).
- Llama Guard 4 12B: harm categories (not injection); licence "other"; context NOT FOUND; needs GPU.
- ShieldGemma-2b: Gemma licence, 4 harm categories, no injection detection; HF repo gated, read from ai.google.dev.
- Sentinel (qualifire): licence "other"/UNVERIFIED; F1 vendor self-reported on own benchmark; context NOT FOUND.
- Latency NOT FOUND for all except Prompt Guard 2. No cross-benchmark comparison read: precision/recall figures are not comparable (different datasets).

## 5. Anthropic provider-native
- Citations: three types (char_location, page_location, content_block_location); "Citations cannot be used together with structured outputs ... the API returns a 400 error"; cited_text "does not count toward output tokens"; streamed as citations_delta; enable on all or none of documents in a request; text only. Fit (c): span-level grounding, but cannot combine with structured output; the app must still run the ADR-009 verifier since citations are model-produced.
- search_result blocks: need type, source, title, content (text only); citations off by default, uniform per request.
- Injection guidance (docs): untrusted content only in tool_result, JSON-encode it, optionally screen tool output with Haiku. Page states no ASR. Confirms ADR-009.
- Anthropic research (anthropic.com/research/prompt-injection-defenses, 2025-11-24): Sonnet 4.5 13.8% -> 1.9%, Opus 4.5 8.0% -> 1.4% ASR with classifiers + safeguards, internal Best-of-N attacker, browser-agent setting; "A 1% attack success rate... still represents meaningful risk." Those classifiers are not offered as an API product in anything read (NOT FOUND).
- Constitutional Classifiers (2025-02-03): jailbreak success 86% -> 4.4%, over-refusals +0.38%, compute +23.7%. API customer availability: NOT FOUND.
- Content moderation guide recommends Haiku for cost; latency NOT FOUND. An LLM check is the 0.5-1.5 s class per ADR-009 evidence, so off the hot path.

## 6. Spotlighting (arXiv 2403.14720)
- Tested on GPT-3.5, text-davinci-003, GPT-4 only; no Claude.
- Delimiting about halves ASR from ~60% baseline; datamarking GPT-3.5 ~50% -> under 3% (text-003 40% -> 0%); encoding to 0.0% (summarization) / 1.8% (Q&A) but hurts weaker models.
- Limits: only a simple keyword attack tested; datamarking bypassed by payloads without spaces; system prompt assumed leaked. Zero cost/latency (prompt transform). Complements, does not replace, tool_result JSON encoding.

## Comparison
| Tool | Cost | p50 latency (stated) | a prompt | b ingest chunks | c output | Licence |
|---|---|---|---|---|---|---|
| Model Armor | free to 2M tok/mo, then $0.10/1M | NOT FOUND (measure) | yes (PI, jailbreak, RAI, SDP detect) | yes, 4 MB doc cap, 1200 QPM | yes (sanitizeModelResponse), detect-only | managed |
| Presidio | CPU only | NOT FOUND (benchmark E4) | yes (PII) | yes (PII) | yes (PII) | MIT |
| NeMo Guardrails | CPU/LLM calls | jailbreak rail 2057 ms CPU / 115 ms GPU | LLM/heavy | poor | partial | Apache-2.0 |
| Prompt Guard 2 86M / 22M | self-host | 92.4 / 19.3 ms A100 (CPU NOT FOUND) | yes | yes with 512-token windows | no | Llama terms (UNVERIFIED) |
| ProtectAI deberta v2 | self-host | NOT FOUND | yes (no jailbreak) | yes | no | Apache-2.0 (archived) |
| Granite Guardian 4.1 8B | GPU | NOT FOUND | harm/groundedness | heavy | yes | Apache-2.0 |
| Qwen3Guard 0.6B | small GPU/CPU? | NOT FOUND | yes (harm, jailbreak, PII) | meh | yes | Apache-2.0 |
| Llama Guard 4 / ShieldGemma | GPU | NOT FOUND | harm only | no | harm only | "other" / Gemma |
| Anthropic citations | output tokens only | n/a | n/a | n/a | grounding spans (no structured output) | API |
| Spotlighting | $0 | ~0 | no (indirect) | n/a | n/a | paper |

## Shortlist per guardrail point
- User prompt: Presidio (PII, in-process) + Model Armor PI/jailbreak (parallel with embed) - as ADR-009; optional Prompt Guard 2 22M only if Model Armor latency or FPR fails (CPU latency must be benchmarked; licence terms UNVERIFIED).
- Ingest chunks: Presidio for PII; Model Armor document screening per document (4 MB, quota-aware batching) for indirect injection; Prompt Guard 2 windows as fallback. Always spotlight/JSON-encode at query time regardless.
- Model output: Presidio sentence-buffered redaction; deterministic citation verifier (ADR-009); Anthropic citations as an additional span signal only if structured output not used; Model Armor response screen optional (detect-only, adds latency).

## Improvements
- ADR-009 500 ms fail-closed timeout and Presidio recall have no vendor numbers: keep E4 benchmark, add Model Armor p50/p95 measurement from Cloud Run region.
- Handle EXECUTION_SKIPPED (over token limit) explicitly: input cap must be <65,536 tokens (<130k for SDP).
- Add document-level Model Armor screening at ingest and datamarking/JSON-encoding of retrieved chunks.
- Model Armor SDP cannot de-identify; do not drop Presidio.
- Presidio default English only; check tenant language needs.

## Gaps
- Model Armor latency, SLA, GA status, precision/recall; Presidio latency and recall; NeMo overhead; Prompt Guard 2 CPU latency; Llama licence terms; Constitutional Classifiers API availability; no Claude figures for Spotlighting - all UNVERIFIED.
- Pricing of Model Armor for ingest volume not modelled (tokens/month of corpus unknown).
