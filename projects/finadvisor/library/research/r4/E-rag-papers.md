EVIDENCE (round 4, Track E + D-research) — v2

READING DEPTH, stated plainly: every number below was read from the ARXIV ABSTRACT only
(tag [ABS]). I read no method or evaluation sections and spawned no page-reader leaves.
Anything tagged [UNVERIFIED] is from memory or an unfetched source and must not go into an
ADR. Arxiv ids in the 2026 range were returned by the arxiv tool; all are preprints unless
noted. For ablation decisions, the abstract-level claims below need a section read first
(listed in Gaps).

Our constraints (read from ADR-008/016, §1.3): hybrid FTS+vector RRF, rerank-2.5-lite,
CRAG-style gate, structure-aware 256-512 children / ~1k parents, contextual retrieval behind
a flag (Haiku batch). Non-goals: no LLM guardrails on hot path, no GraphRAG/RAPTOR/Self-RAG/
SPLADE/ColBERT/HyDE/semantic chunking. TTFT 2.0 s p50 / 3.5 s p95.

---------------------------------------------------------------------------------------
## E6 Chunking / contextual retrieval (most decision-relevant to ADR-016)

### 6a. "Upgrade the Retriever First" (Mangla, arXiv 2603.23533v4, 2026, preprint)
- Idea: tests what a per-chunk LLM call at index time (enrichment, contextual retrieval CR)
  buys over a free structural prefix and a stronger retriever. Pre-registered plan.
- Reported [ABS]: 7B enrichment beats a free section-path prefix under a hybrid retriever by
  +5.5 recall points on Qasper; on FreshStack +2.7, not significant after Holm. Enrichment is
  "equivalent to CR, which sends 5.8-8.7x the input tokens". Qasper answer F1 (7B reader)
  equivalent. Under qwen3-embedding + a reranker (two strongest of eight retrievers) the CI of
  enrichment vs free prefix is inside equivalence margins; under BM25 enrichment gains +8.7.
  Free prefix under a strong retriever beats hybrid enrichment by +3.4 to +6.3. Header-led
  chunks beat 512-char windows; on FreshStack they lose to overlapping 256-token windows.
  Late chunking lowers Qasper recall.
- Dataset: Qasper (scientific QA), FreshStack (technical docs). NOT legal/financial.
- Cost: CR 5.8-8.7x input tokens vs enrichment (relative figure only).
- Assumptions: small readers (7B); English; chunk-level index.
- Fit: our ADR-008 already has the "free prefix" (title + section heading) plus rerank, i.e.
  the configuration where this paper finds CR adds little. Direct support for making L1
  ablation arms: {free prefix, +CR}. Strength of evidence: moderate (pre-registered) but
  off-domain.
- Breaks: gains concentrate under lexical-only retrieval; our FTS leg is not BM25 (ADR-008).

### 6b. Reconstructing Context (Merola, Singh, arXiv 2504.19754, 2025, preprint)
- Compares late chunking vs contextual retrieval. [ABS]: CR "preserves semantic coherence
  more effectively but requires greater computational resources"; late chunking is more
  efficient but "tends to sacrifice relevance and completeness". No numbers in abstract.
- Fit: late chunking needs a long-context embedding model with token-level outputs; Voyage
  API returns one vector per input, so late chunking is NOT available through the API
  [UNVERIFIED for voyage-4; check docs]. Do not ablate it.

### 6c. Late Chunking (Gunther et al., arXiv 2409.04701, 2024, preprint)
- Embed whole document with long-context model, then pool per chunk. Numbers not read.
  Mangla 6a reports late chunking lowers Qasper recall.

### 6d. Financial Report Chunking (Jimeno Yepes et al., arXiv 2402.05131, 2024, preprint)
- Chunk by document element types (from layout model) instead of paragraphs. [ABS]: "element
  type based chunking largely improve RAG results on financial reporting"; no figures in
  abstract. Supports structure-aware chunking (our ADR-008 choice).

### 6e. PDF-to-RAG study (arXiv 2604.04948, 2026, preprint)
- [ABS] 4 converters (Docling, MinerU, Marker, DeepSeek OCR), 21 pipelines, 50 questions over
  36 Portuguese administrative docs (1706 pages). Naive PDFLoader 86.2%; manually curated
  Markdown 91.3%; Docling + hierarchical splitting + image descriptions 94.1 +/- 1.6%.
  Table-dependent questions drive the gap: 33 pp between basic and hierarchical splitting.
  "Metadata enrichment and hierarchy-aware chunking contributed more ... than the conversion
  framework alone." GraphRAG 82% vs 94.1% basic RAG. LLM-as-judge, Wilcoxon over 50 runs.
- Weakness: 50 questions, one corpus, judge-scored. Direction matches ours.

### 6f. LegalBench-RAG (Pipitone, Houir Alami, arXiv 2408.10343, 2024, preprint)
- [ABS] 6,858 human-annotated QA pairs, corpus > 79M chars; mini version for iteration;
  scores precision of minimal snippets. Per-method results not in abstract (UNVERIFIED).
  Use as an external sanity check for chunking arms, English contracts/privacy only, not
  regulation text.

### Anthropic contextual retrieval 35%/49%/67% claim
- NOT CONFIRMED this run (blog not fetched). ADR-016 cites top-20 failure 5.7% -> 2.9%
  (= ~49% relative reduction) and ADR-008 cites 2.9% -> 1.9% for rerank (= ~34%; combined
  5.7 -> 1.9 = ~67%). The 35% figure is, from memory, embeddings-only (5.7 -> 3.7)
  [UNVERIFIED]. Arithmetic is consistent with 49% and 67% as quoted in the ADRs.

---------------------------------------------------------------------------------------
## E1 Tables and structured data

### 1a. Docling / TableFormer (arXiv 2408.09869 tech report; 2501.17887 toolkit)
- [ABS] Docling = DocLayNet layout + TableFormer table structure, MIT, commodity hardware.
  Abstracts give NO TEDS figures. Published TEDS for TableFormer (PubTabNet/FinTabNet,
  CVPR 2022) are [UNVERIFIED]; the Docling report has a TEDS table I did not read.
- Fit: runs offline at ingest, off the TTFT path. Finance-specific failure risk: KID cost
  tables and multi-level headers.

### 1b. VLM table-to-Markdown (arXiv 2508.05669, 2025, preprint)
- [ABS] Fine-tuned Qwen2.5-VL-7B (LoRA, 2,152 image-text pairs) on Malaysian audited
  financial tables: 92.20% criteria accuracy, 96.53% Markdown TEDS on 100 out-of-sample
  tables; says it exceeds GPT-4o and Gemini 2.5 Flash. Baseline TEDS numbers not in abstract.
  Weak evidence (100 tables, one region) but shows the ceiling for a fine-tuned VLM path.

### 1c. HC-RAG (arXiv 2608.12335, 2026, preprint)
- [ABS] Typed evidence graph over 10-K filings (sections, text units, table units),
  intent routing (calculation, trend, fact, comparison). Beats RAPTOR by 6.6 F1 on DocFinQA
  and GraphRAG by 10.9 F1 on its own Multi-Doc-2025 (2,327 QA, 179 10-Ks). Latency/cost not
  in abstract. Idea portable without the graph: section-aware retrieval + intent routing.

### 1d. MimirRAG (arXiv 2605.25030, 2026, preprint)
- [ABS] table-aware chunking, metadata, agent-based retrieval with query planning, hybrid
  search: 89.3% on FinanceBench; ablation names metadata integration, table-aware chunking,
  agentic workflow as the three enablers. Agentic workflow conflicts with our latency budget.

### 1e. FinanceBench (Islam et al., arXiv 2311.11944, 2023)
- [ABS] 10,231 questions; 150-case sample tested on 16 configs; GPT-4-Turbo with a retrieval
  system "incorrectly answered or refused to answer 81%". Long-context helps but costs
  latency. This is the 2023 baseline, since superseded (MimirRAG 89.3%).
- TAT-QA (2105.07624) findings: UNVERIFIED, not searched.

### Structured lookup (text-to-SQL over XBRL / fee tables)
- No paper found this run that compares text-to-SQL over XBRL facts against table chunking
  for fund prospectus data. CSR-RAG (2601.06564) is table retrieval for enterprise
  text-to-SQL: "up to 40% precision, over 80% recall, 30 ms" [ABS], not financial.
- Engineering inference (mine, not a paper): SEC Risk/Return XBRL data is already keyed
  (tag, period, class); deterministic lookup by (fund, class, tag) avoids LLM-generated SQL
  and can be cited by fact id. Ablate as a router arm, not as text-to-SQL.

---------------------------------------------------------------------------------------
## E2 Temporal / "as of" retrieval

### 2a. Temporal Misgrounding in Legal RAG, FiscalQA Pro (arXiv 2608.09393, 2026, preprint)
- Idea: legal QA is temporally indexed retrieval; multi-version index with version selection.
- [ABS] 32,436 article-versions of French tax code (1938-2031); 209 scored questions, 33 CGI
  articles; scoring deterministic (regex, numeric-with-tolerance), no LLM judge. Eleven
  models: parametric 3.0% mean strict accuracy; static current-version RAG 2.7%; static RAG
  retrieves the date-applicable version 0% of the time. Their multi-version retriever (no
  oracle) 98.3% mean strict; oracle-article ablation 99.1%, so residual gap is first-stage
  recall, not version selection.
- Fit: very high. Matches our UK legislation point-in-time and eCFR. Method is index all
  versions with validity intervals and filter by date. Cost = index size (versions x text).
- Caveat: single preprint, French tax code, 209 questions. Numbers are strong, so verify.

### 2b. VersionRAG (arXiv 2510.08109, 2025, preprint)
- [ABS] hierarchical version graph + intent routing. VersionQA 100 questions, 34 versioned
  technical docs: 90% vs naive RAG 58%, GraphRAG 64%; 60% on implicit change detection
  (baselines 0-10%); 97% fewer indexing tokens than GraphRAG. Small benchmark, software docs.
- Filter vs re-rank: both papers support a hard validity filter over re-ranking by
  recency; no head-to-head filter-vs-rerank paper read (UNVERIFIED that none exists).
  TimeQA / TempRALM figures not read.

---------------------------------------------------------------------------------------
## E3 Multi-doc comparison / multi-hop

- Adaptive-RAG (Jeong et al., arXiv 2403.14403, NAACL 2024): [ABS] a small trained
  classifier routes between no-retrieval, single-step and iterative retrieval by query
  complexity; "enhances overall efficiency and accuracy" on open-domain QA. Numbers and
  latency multipliers NOT read.
- IRCoT (2212.10509), Self-Ask (2210.03350): ids from memory, not fetched. Latency
  multipliers UNVERIFIED. Structural fact: each reasoning hop is a sequential LLM call,
  so any loop of >=2 hops cannot meet TTFT p50 2.0 s unless the first token is streamed
  after the final retrieval (my estimate).
- Fit option within budget: single-shot decomposition (one Haiku call producing N
  sub-queries, retrieve in parallel, one generation) rather than iterative loops. No paper
  read comparing this against IRCoT on latency. RIT-RAG (2610.11370) is an agentic tree
  navigator [ABS: +6.6 to 11.4 pts on EntQABench]; agentic, so outside budget.

---------------------------------------------------------------------------------------
## E4 Multilingual / cross-lingual EU legal retrieval

- LEMUR (arXiv 2602.09570, 2026, preprint) [ABS]: 24,953 EUR-Lex PDFs, 25 languages;
  fine-tuning three multilingual embedders consistently improves top-k, most for
  low-resource languages; gains transfer cross-lingually. No numbers in abstract. Note: it
  also measures PDF-vs-HTML fidelity, supporting our use of EUR-Lex HTML over PDF.
- ChemCLIR-Bench (2609.23231) [ABS]: best model Recall@10 falls 0.72 -> 0.53 when query and
  document languages differ; some models strong monolingual collapse cross-lingually. Not
  legal, but shows the gap is real and model-dependent, so measure ours.
- Voyage voyage-4 MTEB/MMTEB numbers: NOT fetched. UNVERIFIED. Need Voyage blog/docs.
- Recommended arm: EN query vs EN-only / DE / FR docs with the same questions; also a
  "translate query to doc language" arm (extra Haiku call) as a baseline.

---------------------------------------------------------------------------------------
## E5 Span-level citations and verification

- ALCE (Gao et al., arXiv 2305.14627, EMNLP 2023) [ABS]: benchmark with fluency,
  correctness, citation quality; on ELI5 "even the best models lack complete citation
  support 50% of the time". Numeric P/R of its NLI-based citation recall/precision not read.
- Citation granularity (arXiv 2604.01432, 2026, preprint) [ABS]: forcing sentence-level
  citations forfeits 2-97% (median 40%) vs best granularity; attribution quality peaks at
  paragraph level; answer correctness changes only -2.3% to +4.4%. Implication: span-level
  citations may reduce attribution quality for synthesis questions; ablate paragraph vs
  sentence cite granularity.
- VeriCite (2510.11394) [ABS]: initial answer -> NLI claim check -> evidence selection ->
  refinement; "significantly improves citation quality" (no figures). Multiple LLM stages,
  too slow for hot path; usable as an async/post-hoc check.
- FinRegQA-EU (2609.36856, 2026) [ABS]: EBA/ESMA Q&A; LLM judges rewarded citation density
  (SFT highest judge score, lowest rule-based Citation F1, 3x citations mostly unsupported).
  Important for E7: do not trust an LLM judge alone for citation quality; add a rule-based
  citation-existence/ID check.
- Anthropic Citations API precision/recall: no published figures read (UNVERIFIED).

---------------------------------------------------------------------------------------
## D-research: prompt-injection defenses and numeric grounding

- Spotlighting (Hines et al., arXiv 2403.14720, Microsoft, 2024) [ABS]: delimiting /
  datamarking / encoding of untrusted input; ASR "from greater than 50% to below 2%" on GPT
  family models, "minimal detrimental impact" on tasks. Zero extra latency (prompt-only).
  FPR n/a (not a detector). Weakness: static attacks; adaptive attacks not in abstract.
  Fit: yes, free, no LLM call. Compatible with §1.3.
- InjecGuard / PIGuard (Li, Liu, arXiv 2410.22770, 2024) [ABS]: over-defense is the problem:
  existing guard models drop to ~60% accuracy (near random) on NotInject (339 benign
  samples with trigger words); InjecGuard beats the best existing model by 30.8%. FPR
  figures not in abstract. Fit: a small classifier on retrieved chunks at ingest or retrieval
  (not an LLM on the hot path); regulatory text contains words like "ignore", "instruction",
  "must", so over-defense risk is real here.
- DataSentinel (Liu et al., arXiv 2504.11358, IEEE S&P 2025) [ABS]: fine-tuned LLM detector,
  minimax training vs adaptive attacks; "effectively detects" existing and adaptive attacks
  (numbers not in abstract). It is an LLM call per input, so ingest-time only for us.
  ToolHijacker (2504.19793) [ABS] says DataSentinel, perplexity detection and StruQ/SecAlign
  were "insufficient" against its tool-selection attack, i.e. detectors are not complete.
- PromptGuard (Meta), Instruction Hierarchy (2404.13208), BIPIA (2312.14197), AgentDojo
  (2406.13352): not fetched; ASR/FPR UNVERIFIED.
- Numeric grounding: FinGround (arXiv 2604.23588, 2026, preprint) [ABS]: atomic claims
  typed by a six-type financial taxonomy and verified by type-routed strategies including
  formula reconstruction; under identical retrieval cuts hallucination rate 68% vs the
  strongest baseline (p<0.01), 78% vs GPT-4o; an 8B distilled detector keeps 91.4% F1 at
  18x lower per-claim latency, $0.003/query. Says existing detectors miss 43% of
  computational errors. Claim of "every number appears in a cited span" as a plain
  deterministic check: no dedicated paper found; FiscalQA (2608.09393) scores with
  regex/numeric-with-tolerance nuggets, a precedent for deterministic numeric matching.
  Our regex+span-match gate is a own design, to be validated on the eval set (false
  rejects from derived numbers, rounding, unit/locale differences DE/FR "1.234,56").

---------------------------------------------------------------------------------------
## E7 Ablation design on 150-300 items

- Mangla 2603.23533 is a template: pre-registered plan, Holm adjustment, equivalence
  margins (TOST-style) rather than "not significant" for "no difference".
- Arawjo evalstats (arXiv 2609.35815, 2026, preprint) [ABS]: running statistics on raw LLM
  judge scores inflates false positives; false-positive risk peaks at "almost perfect"
  human-LLM agreement; for N<100 gives CI/p-value recommendations and "warn[s] against
  bootstrap CIs"; uses prediction-powered inference with a human-labelled calibration set.
  Tension with plain bootstrap: at N=150-300 bootstrap is less risky than N<100, but the
  paper's caution applies to judge-scored metrics.
- Sartori & Garcia (arXiv 2605.27789) [ABS]: fixed budget, cluster-aware inference; a
  binomial test made all four comparisons look significant, cluster-aware left one
  Bonferroni-significant. Lesson: cluster by source document/regulation when several
  questions share a document.
- "Noisy but Valid" (2601.20913) [ABS]: calibrate judge TPR/FPR on a small human-labelled
  set to get valid tests.
- Eval-Pair Matrix (2607.10626) [ABS]: same-family judge self-leniency effect ~0
  (-0.5 pp, CI [-2.7, +1.7]) on 275 records, so judge by a different family is cheap insurance
  not a necessity.
- Practical protocol (my synthesis): paired design (same items in all arms); binary metrics
  (correct, cited-correctly, retrieval hit@k) -> McNemar exact test on discordant pairs;
  continuous (nDCG, recall) -> paired bootstrap CI over items, resampling clusters
  (document/regulation); Holm across arms; human-label 50-100 items to calibrate the judge
  and report judge-human kappa; add deterministic checks (cited ID exists, numbers in span).
  Power note: with 200 items and ~10% discordance, McNemar detects roughly a 7-8 pp swing;
  smaller effects are not detectable, so only large arms are worth ablating [my estimate,
  not computed from data].

---------------------------------------------------------------------------------------
## Recommended candidates for ablation (L1)
1. Free structural prefix (title + section path) vs + contextual retrieval (ADR-016 flag).
   Evidence: 2603.23533 says CR ~ enrichment ~ free prefix under strong retriever+rerank.
   Predict small or no gain; cost 5.8-8.7x tokens. Keep the flag default OFF until it wins.
2. Temporal: hard validity-interval filter on versioned sources vs no filter (static
   current-version). Evidence 2608.09393 (0% date-applicable retrieval for static). No LLM
   cost. Very likely to win; ship as correctness, not optional.
3. Table handling: markdown table chunk with caption/header repetition vs deterministic
   XBRL fact lookup router for Risk/Return numbers; Docling as the PDF extractor, with
   TEDS spot check on 20 KID cost tables. Evidence: 6e (33 pp swing from splitting), 1b.
4. Multi-doc: single-shot Haiku decomposition into parallel sub-queries vs plain retrieval,
   only on comparison questions; skip iterative IRCoT/agentic loops (budget).
5. Cross-lingual: EN query against DE/FR docs with voyage-4 directly vs query translation.
6. Citations: paragraph vs sentence granularity (2604.01432) plus deterministic cited-ID
   and numeric-in-span checks (rule-based, not LLM judge; cf. 2609.36856).
7. Injection: spotlighting (free) as default; add a small classifier (InjecGuard-class) only
   at ingest and measure false positives on regulatory text. No LLM detector at request time.

## Gaps:
- Anthropic 35/49/67% not confirmed from the source blog.
- Docling/TableFormer TEDS figures, TAT-QA, text-to-SQL-vs-chunking on XBRL: not found.
- Voyage voyage-4 MTEB/MMTEB/multilingual numbers; Voyage API token-level output for late
  chunking: not checked.
- IRCoT, Self-Ask, Adaptive-RAG latency multipliers and accuracy: not read.
- PromptGuard, Instruction Hierarchy, BIPIA, AgentDojo ASR/FPR; DataSentinel and PIGuard
  FPR figures: abstracts give none.
- ALCE citation precision/recall, AlignScore/NLI checker accuracy, Anthropic Citations API
  figures: not read.
- TimeQA/TempRALM and any direct filter-vs-rerank study: not searched.
- All methods/evaluation sections unread; 2026 preprints (2608.09393, 2603.23533,
  2604.23588, 2609.35815) are single-source and load-bearing, so fetch their results
  sections via page-reader before citing numbers in an ADR.
