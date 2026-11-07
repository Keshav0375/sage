# Round 4, Track A: eval and guardrail datasets (FinAdvisor)

Read date for every source below: 2026-11-01. Version is the dataset card or page state on that date.
Method note: the page-reader leaf was not used. I read the dataset cards, GitHub files and arXiv pages myself, and quote only text I saw. Items I could not verify are marked UNVERIFIED.
Licences on HF are the card metadata unless stated. A paper licence (arXiv) is not the data licence.

EVIDENCE

## Part 1. Financial QA / RAG benchmarks

Summary table (compliance fit: High = regulatory text; Low = 10-K numerics).

| Set | Licence (data) | Commercial? | Size | Docs included | Task | Compliance fit |
|---|---|---|---|---|---|---|
| FinanceBench | CC-BY-NC-4.0 (HF card) | No | 150 open of 10,231 | Yes (PDFs in GitHub repo) | Open-book QA over SEC filings | Low |
| FinQA | CC-BY-4.0 (HF); MIT (GitHub repo) | Yes | 8,281 | Context is excerpts | Numeric reasoning, table+text | Low |
| TAT-QA | CC-BY-4.0 (HF); MIT (GitHub) | Yes | 16,552 Q | Context included | Hybrid table+text numeric | Low |
| ConvFinQA | MIT (GitHub repo); no HF card checked | Yes (repo licence) | 3,892 conv / 14,115 Q | Context included | Conversational numeric | Low |
| DocFinQA | MIT (HF) | Yes | 7,437 Q | Full filings | Long-context QA | Low |
| FinDER | CC-BY-NC-4.0 (HF) | No | 5,703 | Evidence passages | Retrieval + QA, 10-K | Low-medium |
| FinTextQA | CC-BY-NC-SA-4.0 (HF) | No | 1,262 | Not verified | Long-form QA, textbooks + gov sites | Medium |
| SEC-QA | Data licence UNVERIFIED | UNVERIFIED | Generation framework | Not verified | Multi-doc generated QA | Low |
| FinanceRAG (ICAIF 24) | Kaggle terms, UNVERIFIED | UNVERIFIED | 7 subsets | Corpora yes | Retrieval | Low |
| ObliQA | Apache-2.0 (HF) | Yes | 27,869 | Yes (40 ADGM docs) | Regulatory retrieval + answer | High (UAE, not US/EU/UK) |
| ObliQA-MP | Apache-2.0 (HF) | Yes | 2,976 | Same corpus | Multi-passage regulatory | High |
| ObliQA-XRef | "other" (HF) | UNVERIFIED | 17,394 combined | Passages in rows | Cross-reference QA, ADGM + UK PRA Rulebook | High (UK) |
| LegalBench-RAG | Repo MIT; per-subset source terms apply | Mixed | 6,858 Q | Yes (download) | Legal retrieval | Low (contracts) |
| EU2UK / UK2EU RegIR | CC-BY-NC-SA-4.0 | No | 1,700 + 1,800 queries | Yes | Doc-to-doc retrieval, EU/UK law | Medium |
| FinBen en-regulations | MIT (HF), gated auto | Yes | 254 test | Context in row | Long-form regulation QA | Medium |
| MultiFinBen PolyFiQA | MIT / Apache-2.0 (cards disagree) | Yes | 76 (Expert) | In row | Multilingual financial QA | Low |

### FinanceBench
- Source: https://huggingface.co/datasets/PatronusAI/financebench ; https://github.com/patronus-ai/financebench ; paper https://arxiv.org/abs/2311.11944
- Licence: HF card metadata "license:cc-by-nc-4.0". Not commercial. The GitHub API returned no licence file for the repo (UNVERIFIED terms there). The paper itself is "License: CC BY-NC-ND 4.0" (https://arxiv.org/html/2311.11944). (read 2026-11-01)
- Size: "FinanceBench comprises 10,231 cases, of which 150 are used for expert evaluation and are available open-source." (arXiv HTML Appendix C). "This is an open source sample of 150 annotated examples" (HF card).
- Docs: "The relevant financial source documents (PDFs) are located in /pdfs/" (GitHub README). "40 companies ... and 361 public filings, released between 2015 and 2023, including 10Ks, 10Qs, 8Ks, and Earnings Reports."
- Task: open-book QA; 66% numerical reasoning, 28% extraction, 6% logical (paper). Fields include evidence text, page number, justification.
- Annotation protocol: 25 domain-relevant question templates "developed with our team of financial analysts and refined by reviewing companies' public findings (e.g. 10Ks) and interviewing financial experts"; plus "novel generated questions" written by annotators, told to make them "realistic ... varied ...".
- Limits it states: "sometimes the correct answer is ambiguous ... some gold ..." answers are debatable.
- Fit: Low for compliance. Useful as a protocol model and as a 10-K sanity set. The NC licence blocks a public demo repo redistributing it (linking to it is fine).

### FinQA
- https://huggingface.co/datasets/ibm-research/finqa (card: license cc-by-4.0, en); https://github.com/czyssrs/FinQA (GitHub API: MIT). Paper https://arxiv.org/abs/2109.00122
- Quote: "FinQA, a expert-annotated dataset that contains 8,281 financial QA pairs ... Eleven finance professionals collectively constructed FinQA based on the earnings reports of S&P 500 companies" (arXiv HTML).
- Task: numeric reasoning with program annotations, tables + text. Docs: report excerpts only. Fit: Low.

### TAT-QA
- https://huggingface.co/datasets/next-tat/TAT-QA (cc-by-4.0); https://github.com/NExTplusplus/TAT-QA (GitHub API: MIT).
- Quote: "TAT-QA contains 16,552 questions associated with 2,757 hybrid contexts from 182 reports" (arXiv 2105.07624 HTML). Task: hybrid table+text, numeric. Fit: Low.

### ConvFinQA
- https://github.com/czyssrs/ConvFinQA (GitHub API: MIT). Paper https://arxiv.org/abs/2210.03849.
- Quote: "3,892 conversations consisting 14,115 questions" and "3,037/421/434 for train/dev/test". Built from FinQA. Fit: Low. (An unofficial HF mirror, ChanceFocus/flare-convfinqa, has no licence on its card; do not use.)

### DocFinQA
- https://huggingface.co/datasets/kensho/DocFinQA (license: mit; 1K-10K rows). Paper https://arxiv.org/abs/2401.06915.
- Quote: "We augment 7,437 questions from the existing FinQA dataset with the full-document context, extending the average context length from under 700 words in FinQA to 123k words". Full filings included. Fit: Low, but good for long-document retrieval stress.

### FinDER (2025)
- https://huggingface.co/datasets/Linq-AI-Research/FinDER (license cc-by-nc-4.0); paper https://arxiv.org/abs/2504.15800.
- Quote: "5,703 expert-annotated query-evidence-answer triplets derived from real-world 10-K filings and ambiguous financial queries submitted by industry professionals." Short, acronym-heavy queries. Not commercial. Fit: Low-medium (realistic terse queries, but 10-K).

### FinTextQA (2024)
- https://huggingface.co/datasets/GPS-Lab/FinTextQA (license cc-by-nc-sa-4.0); https://arxiv.org/abs/2405.09980.
- Quote: "1,262 high-quality, source-attributed QA pairs extracted and selected from finance textbooks and government agency websites." Long-form. NC + share-alike. Fit: Medium (regulatory-adjacent content, but textbooks).

### SEC-QA (2024)
- Paper https://arxiv.org/abs/2406.14394 (paper licence "CC BY-NC-SA 4.0"). Quote: "a continuous dataset generation framework with ... semi-automatic generation of Question-Answer (QA) pairs spanning multiple long context financial documents". I found no data repository or data licence: UNVERIFIED. Fit: Low.

### FinanceRAG / ICAIF 2024 challenge
- https://finance-rag.com/ ; the HF repo it names, Linq-AI-Research/FinanceRAG, was not found by the HF tools on 2026-11-01 (UNVERIFIED availability). Data came via Kaggle competition "icaif-24-finance-rag-challenge" (https://github.com/cv-lee/FinanceRAG/blob/main/prepare_dataset.py); Kaggle terms not read: UNVERIFIED.
- Composition (https://arxiv.org/html/2411.16732): FinDER, FinQABench, FinanceBench, TATQA, FinQA, ConvFinQA, MultiHiertt. Only retrieval was scored: "only Task 1 [Retrieval] is within the scope of this challenge". It is a repackaging of sets above, so their licences bind (FinanceBench and FinDER are NC). Fit: Low.

### Regulatory QA
- ObliQA: https://huggingface.co/datasets/RegNLP/ObliQA (API: license apache-2.0, last modified 2026-02-24). "27,869 synthetic question-answer pairs grounded in obligation-containing passages from a 40-document financial regulation corpus" (ADGM, Abu Dhabi). Construction: "LLM-based question generation + NLI-based filtering". Own limitation list: "Synthetic questions: phrasing may differ from real compliance-user queries ... best used as a benchmarking resource, not as a substitute for expert legal annotation." Source docs: structured passages in https://github.com/RegNLP/ObliQADataset. Paper https://arxiv.org/abs/2409.05677 (RIRAG); shared task https://aclanthology.org/2025.regnlp-1.1/.
- ObliQA-MP: https://huggingface.co/datasets/RegNLP/ObliQA-MP , apache-2.0, 2,976 pairs (2,083/446/447), labels are LLM-made: "LLM-based connectivity labels ... not expert adjudication".
- ObliQA-XRef: https://huggingface.co/datasets/RegNLP/ObliQA-XRef , card licence "other" (terms not read: UNVERIFIED), ADGM 4,992 + UK PRA Rulebook 12,402 (17,394 deduped). Quote: "Users must respect the licensing, access, and redistribution terms of the underlying regulatory corpora, including the ADGM and UK Prudential Regulation Authority Rulebook". `expected_answer` is "a validated synthetic reference answer ... not ... a human-authored gold answer."
- EU2UK/UK2EU RegIR: https://huggingface.co/datasets/community-datasets/eu_regulatory_ir , cc-by-nc-sa-4.0; EU2UK 1,400/300/300 queries over 52,515 UK regulations; UK2EU 1,500/300/300 over 3,930 EU directives. Retrieval only (document to document), no answers.
- FinBen Regulations: https://huggingface.co/datasets/TheFinAI/en-regulations , license mit, gated auto, 254 test rows, long-form regulatory QA scored by ROUGE/BERTScore.
- LegalBench-RAG: https://arxiv.org/abs/2408.10343 ; repo https://github.com/zeroentropy-ai/legalbenchrag (MIT). Quote: "6,858 query-answer pairs over a corpus of over 79M characters, entirely human-annotated by legal experts"; mini = 776 queries. Sources are ContractNLI, CUAD, MAUD, PrivacyQA: "Please ensure you agree to the usage policies of ContractNLI, CUAD, MAUD, and PrivacyQA". Contracts and privacy policies, not financial regulation. Fit: Low; useful only for retrieval-precision method (snippet-level ground truth).
- COLIEE-like / COLING-2025 Regulations Challenge: https://coling2025regulations.thefin.ai/dataset lists data sources only; no released question set verified. UNVERIFIED. COLIEE itself not read.
- Finding: no public human-verified QA set covers US (SEC/FINRA), EU (MiFID II) or UK (FCA) advisor regulation with real gold answers. The nearest are ADGM and UK PRA (synthetic). FinAdvisor must build its own (Part 2).

### Multilingual financial QA
- MultiFinBen: https://github.com/xueqingpeng/MultiFinBen (Apache-2.0 repo; "All datasets are released under the MIT License unless otherwise specified"); paper https://arxiv.org/abs/2506.14028. Languages: English, Chinese, Japanese, Spanish, Greek. No French/German/Italian. PolyFiQA-Expert is 76 examples (card says license mit in metadata and "Apache License 2.0" in text: conflict, UNVERIFIED which applies). Fit: Low.

## Part 2. Building a real golden set

### Published methods
- Ragas: https://docs.ragas.io/en/stable/concepts/test_data_generation/rag/ builds a knowledge graph from documents, with single-hop and multi-hop, specific or abstract queries. "The page makes no statement about human review or verification" (my reading of the page) and gives no recommended size. Paper https://arxiv.org/abs/2309.15217 is reference-free metrics, "without having to rely on ground truth human annotations". So Ragas generation gives candidates, and the human check is yours to add.
- ARES: https://arxiv.org/abs/2311.09476 "ARES accurately evaluates RAG systems while using only a few hundred human annotations during evaluation", via "prediction-powered inference (PPI)" on "a small set of human-annotated datapoints". This supports a few hundred human labels as a calibration set for an LLM judge.
- ObliQA pipeline (synthetic generation then NLI filter) and its own caveat that this is not expert annotation (above).
- FinanceBench protocol: finance analysts wrote question templates and novel questions, each with evidence string + page number + optional justification; then 150 cases were reviewed by experts against 16 configurations (n=2,400 manual reviews) (arXiv 2311.11944). The paper does not describe a second-annotator agreement step in the text I searched: UNVERIFIED.
- LegalBench-RAG: human-annotated snippet-level ground truth (character ranges in source text).

### Size for statistically useful pass lines
- Source: Miller, "Adding Error Bars to Evals", https://arxiv.org/abs/2411.00640. Quotes: "SE_Bernoulli = sqrt(s(1-s)/n)" (eq. 2); "CI_95% = s +/- 1.96 x SE" (eq. 3); recommends reporting "the number of questions in each eval, and the standard error of each estimate"; recommends paired analysis for comparing models; sample-size formula from alpha, power and minimum detectable effect (Section 5); and a clustered-SE adjustment when questions are non-independent (Section 2.2; relevant if several questions come from one document).
- My arithmetic from eq. 2-3 (not in the paper; check before citing): 95% half-width at pass rate 0.90 is +/-4.8 pp at n=150, +/-4.2 at n=200, +/-3.4 at n=300. At 0.80: +/-6.4 / 5.5 / 4.5 pp. Unpaired detection of a 10 pp gap at ~80% baseline, alpha 0.05, power 0.8, needs about 250 per arm; a 5 pp gap needs about 1,000 per arm. Paired comparison on the same items needs fewer.
- Zero-failure rule ("rule of three", my addition, not from a read source): to claim a failure rate below 2% at 95% with zero observed failures needs about 150 items; below 1% about 300.
- Implication: 150-300 items gives pass lines with roughly +/-3.5 to 5 pp error. Fine for gating a release at coarse thresholds and for catching large regressions. Not enough to rank two similar configurations by 2-3 pp. Cluster by source document when computing the CI (items from one document are not independent), and report n and SE per slice. Slices below ~30 items (e.g. one jurisdiction) give only directional signals.

### Labelling budget for one person (ESTIMATE, not sourced; assumptions stated)
Assumptions: Keshav is not a compliance lawyer, uses real documents (SEC/FINRA rules, MiFID II/ESMA, FCA Handbook, sample prospectuses, sample advisor disclosures), generates candidates with an LLM, then checks each. Per item: locate evidence in the source 4-6 min, verify or rewrite the gold answer 3-5 min, tag jurisdiction/type/answerable 1 min = 8-12 min. Add document prep and chunking (one-off 6-10 h), prompt/generator tuning (4 h), discard rate 30-40% of generated candidates (so generate about 1.5x), and 10% re-check for self-consistency (1-2 min each).

| Checked items | Labelling h | Overheads h | Total h (about) |
|---|---|---|---|
| 150 | 20-30 | 12-16 | 32-46 |
| 200 | 27-40 | 12-16 | 39-56 |
| 300 | 40-60 | 14-18 | 54-78 |

Add 20-40% if Keshav must read unfamiliar regulation closely, and include refusal and out-of-scope items (which are fast, 3-4 min). Single labeller means no inter-annotator agreement; budget a second reviewer on a 10-15% sample if anyone is available, else report that the set has one labeller.

### Plan implied by the sources
1. Take 40-60 real documents across US/EU/UK and tenants. Keep the source files or URLs and hashes in the repo (public documents only, check each licence).
2. Generate candidate questions with an LLM (Ragas-style single and multi-hop, plus advisor-style persona queries). Add hand-written questions for the compliance cases the generators miss.
3. Human-check every item in the golden set: question realistic, evidence span located, gold answer correct, answerable or not. Store the evidence span (FinanceBench / LegalBench-RAG style).
4. Include unanswerable, cross-jurisdiction and conflicting-source items. These are not covered by public sets.
5. Use a small LLM-judge calibration set (ARES-style, a few hundred labels) only if you later want to scale with automatic judging.
6. Use ObliQA as an external retrieval smoke test (Apache-2.0), not as the pass line.

## Part 3. Guardrail eval sets

| Set | Link | Licence | Size | Languages | Labels |
|---|---|---|---|---|---|
| ai4privacy pii-masking-200k | https://huggingface.co/datasets/ai4privacy/pii-masking-200k | "other" | 100K-1M rows (card) | en, fr, de, it | PII spans |
| ai4privacy pii-masking-300k | https://huggingface.co/datasets/ai4privacy/pii-masking-300k | "other", see below | 100K-1M | en, fr, de, it, es, nl | PII spans; includes FinPII-80k |
| ai4privacy pii-masking-400k | .../pii-masking-400k | "other", same terms | 100K-1M | en, fr, de, it, es, nl | PII spans |
| ai4privacy openpii-1m | .../pii-masking-openpii-1m | metadata "other" + license_name cc-by-4.0 | ~1.4M | 23 | 19 PII classes |
| ai4privacy openpii-1.5m | .../pii-masking-openpii-1.5m | CC-BY-4.0 stated in card text | 1,636,375 | 30 | 19 PII classes, BIO labels |
| Gretel synthetic_pii_finance_multilingual | https://huggingface.co/datasets/gretelai/synthetic_pii_finance_multilingual | apache-2.0 | 55,940 records | en, fr, de, nl, es, it | 29 PII types, 100 financial document formats |
| deepset/prompt-injections | https://huggingface.co/datasets/deepset/prompt-injections | apache-2.0 | 662 (546 train / 116 test) | UNVERIFIED | binary injection label |
| Lakera gandalf_ignore_instructions | https://huggingface.co/datasets/Lakera/gandalf_ignore_instructions | mit | 1,000 (777/111/112) | en | injection prompts with similarity score |
| Lakera mosscap_prompt_injection | https://huggingface.co/datasets/Lakera/mosscap_prompt_injection | mit | 100K-1M | en | all prompts, many not true injections |
| Lakera gandalf_summarization | https://huggingface.co/datasets/Lakera/gandalf_summarization | mit | not read | not read | injections via summarization task |
| JailbreakBench JBB-Behaviors | https://huggingface.co/datasets/JailbreakBench/JBB-Behaviors | mit | 100 harmful + 100 benign behaviors | en | behavior category |
| HarmBench behaviors | https://huggingface.co/datasets/walledai/HarmBench | mit, gated | <1K | en | behavior prompts |
| Qualifire / rogue-security prompt-injections-benchmark | https://huggingface.co/datasets/rogue-security/prompt-injections-benchmark | cc-by-nc-4.0, gated | 5,000 | not stated | jailbreak / benign |
| PromptShield | https://huggingface.co/datasets/hendzh/PromptShield | apache-2.0 (API) | not read | en | text classification; card not read |
| PINT benchmark | https://github.com/lakeraai/pint-benchmark | repo MIT | 4,314 inputs (3,016 en, 1,298 non-en) | many | injection / jailbreak / benign hard negatives |
| BIPIA | https://github.com/microsoft/BIPIA | MIT text; GitHub API says NOASSERTION | 5 tasks | en | indirect injection in email/web/table/code/abstract |
| InjecAgent | https://github.com/uiuc-kang-lab/InjecAgent | MIT | 1,054 cases | en | attacker intent: direct harm / data exfiltration |
| AgentDojo | https://github.com/ethz-spylab/agentdojo | MIT | 97 tasks, 629 security cases | en | environment, not a static set |
| LLMail-Inject | https://huggingface.co/datasets/microsoft/llmail-inject-challenge | mit | 208,095 attack prompts | en | attacks vs email RAG + tool call |

### PII details
- ai4privacy 200k/300k/400k: card text "Academic use is encouraged with proper citation provided it follows similar license terms. Commercial entities should contact us at licensing@ai4privacy.com for licensing inquiries" and "See LICENSE.md for full details" (300k and 400k cards). I could not retrieve the license.md file ("Entry not found" on raw fetch), so the exact terms are UNVERIFIED. Treat as non-commercial and not redistributable in a public repo until read.
- 300k: "split into 2 sub-datasets: OpenPII-220k and FinPII-80k. The FinPII includes additional classes specific to Finance and Insurance"; extended classes require contacting licensing@ai4privacy.com, so the finance-specific classes are not freely usable.
- openpii-1.5m card text: "License: CC-BY-4.0 ... Permitted Use: Research, commercial use, redistribution, and modification, subject to attribution." Its HF metadata says license "other" with license_name cc-by-4.0, so cite the card text. Covers 19 core labels (e.g. CREDITCARDNUMBER, TAXNUM, SOCIALNUM, IDCARDNUM, PASSPORTNUM, EMAIL, TELEPHONENUM, names, addresses, DATE). Synthetic; no finance-specific classes such as IBAN or account number.
- Gretel finance: Apache-2.0, synthetic, 29 PII types, "100 distinct financial document formats". Closest in document type to financial advisor material. Labels were LLM-generated and checked by GLiNER (card: "double-check and validate the labeled PII spans"), so label noise is possible.

### Direct injection details
- deepset/prompt-injections: the card header has both "license: apache-2.0" and a nested "license: cc-by-4.0" in dataset_info; conflicting, so Apache-2.0 per the top-level metadata, with a note to confirm. Tiny (116 test rows), so wide error bars; use only as a smoke test.
- Lakera Gandalf ignore_instructions: derived "from all prompts submitted to Gandalf in July 2023" filtered by embedding similarity to "ignore instructions". Short, English, one attack family. Mosscap is unfiltered ("we release every prompt ... regardless of whether it truly is a prompt injection") so it needs cleaning before it can serve as labelled attacks.
- JailbreakBench / HarmBench: these are harmful-request behaviors (weapons, hate, etc.), not instruction-override attacks on a RAG assistant. Low relevance for compliance. JBB benign behaviors help measure over-refusal.
- Qualifire / rogue-security: CC-BY-NC, gated; excluded for a public repo.
- PINT: the README describes the composition, including benign hard negatives, "chats between users and agents" and "benign inputs taken from public documents". I did not find the data file in the repo, only the notebook and an example YAML; whether the real set is public is UNVERIFIED (its stated purpose is a private neutral benchmark). Use its YAML format and its score table (scores dated 2025-05 to 2025-08) as a reference, not as a dataset.
- 2025-2026 sets: PromptShield (Apache-2.0 per API) found via search but its card was not read. I did not search other 2025-2026 sets further (e.g. WildJailbreak is odc-by and gated auto, 100M-1B rows size category, not evaluated for fit). UNVERIFIED coverage.

### Indirect injection details
- BIPIA: https://arxiv.org/abs/2312.14197 . The repo licence file is MIT text, but the README says the Web QA and Summarization contexts "due to license reasons, require users to read the usage terms of the source data and download it from the source"; Email QA data comes from OpenAI Evals, Table QA from WikiTableQuestions, Code QA from Stack Exchange. Usable for a document-embedded test pattern; redistribution of context data is restricted.
- InjecAgent: "1,054 test cases covering 17 different user tools and 62 attacker tools" (arXiv 2403.02691). Tool-using agents, not document RAG.
- AgentDojo: "97 realistic tasks ... 629 security test cases" (arXiv 2406.13352); a runnable environment, heavy to adapt to a RAG assistant.
- LLMail-Inject: "208,095 distinct human-written attack prompts collected through a public red-teaming challenge with 839 participants" where "prompts must be retrieved from an email database, evade production-level defenses, and trigger unauthorized tool calls" (arXiv 2506.09956). MIT. Closest in shape to retrieval-poisoned documents. Email text, so wrap attack strings into financial document chunks yourself.
- Toxic / off-topic for financial advice: not researched in this round (gap).

## Confirms
- A real, human-checked, public compliance golden set for US/EU/UK advisor regulation does not exist in anything read; the synthetic ObliQA family is the nearest, and its own cards say it is not expert annotation.
- 150-300 checked items give about +/-3.5 to 5 pp at 95% (my arithmetic on Miller eq. 2-3).

## Contradicts
- None of the "newer" financial sets (FinDER, FinTextQA, FinanceBench) are commercially usable: all NC. Common assumption that they could seed a public repo is wrong.
- ai4privacy "200k/300k/400k" are not under an open licence; only the newer openpii-1m/1.5m state CC-BY-4.0.

## Limits
- Licence conflicts to resolve before use: deepset (apache vs cc-by in one card), PolyFiQA (mit vs apache), openpii-1m metadata.
- FinanceRAG corpora were not retrievable via HF; Kaggle terms unread.

## Vendor recommends
- ObliQA cards: use for "retrieval benchmarking" and "RAG answer generation", report Recall@10, MAP@10, nDCG@10, and treat as a benchmark "not ... a substitute for expert legal annotation".
- Miller: report n and SE; use paired analysis; run power analysis for the sample size.

## Changes
- ObliQA cards updated 2026-02-24 (HF API); ObliQA-XRef 2026-05-09 adds UK PRA Rulebook. OpenPII flagship is now 1.5M (card updated 2026-06-03).
- FinanceBench HF card last updated 2024-11-17; open sample still 150.

## Recommended set (for a public demo repo)

| Role | Pick | Licence | Public repo OK? |
|---|---|---|---|
| QA benchmark 1 (retrieval smoke test, regulatory) | ObliQA / ObliQA-MP (test splits) | Apache-2.0 | Yes, with attribution; do not rely on it for the pass line |
| QA benchmark 2 | None. Skip FinanceBench/FinDER/FinTextQA (NC). Optional: FinQA/DocFinQA (CC-BY-4.0 / MIT) only if numeric tables matter | CC-BY-4.0 / MIT | Yes |
| Real golden set | Own 150-300 items from public regulatory documents (plan above); about 55-80 h | Your own; confirm each source document's reuse terms | Yes, if sources allow |
| PII | ai4privacy openpii-1.5m (CC-BY-4.0 per card text); add Gretel finance (Apache-2.0) for financial document formats | CC-BY-4.0 / Apache-2.0 | Yes, with attribution |
| Direct injection 1 | Lakera gandalf_ignore_instructions (MIT) | MIT | Yes |
| Direct injection 2 | deepset/prompt-injections (Apache-2.0, confirm card) | Apache-2.0 | Yes; tiny, smoke test only |
| Indirect injection | LLMail-Inject (MIT), wrap attack strings into financial document chunks; optionally BIPIA patterns only (not its restricted contexts) | MIT | Yes |

Excluded: FinanceBench, FinDER, FinTextQA, Qualifire, EU2UK/UK2EU (all NC); ai4privacy 200k/300k/400k (terms unread, commercial needs a licence); PINT data (not found public).

Improvements:
- Build the golden set from real documents with the evidence span stored per item, and slice by jurisdiction; report n and SE for every pass line.
- Add unanswerable, cross-jurisdiction and prompt-injection-in-document items to the golden set itself, since no public set covers them.
- Use paired comparison on the same items when comparing two configurations.
- Re-run the licence check on the exact dataset revision at integration time and record it.

Gaps:
- ai4privacy license.md text (200k/300k/400k) not retrieved.
- SEC-QA data licence and availability; FinanceRAG Kaggle terms; ObliQA-XRef licence terms; COLIEE; EUR-Lex-based QA sets (only RegIR retrieval found).
- deepset languages; PromptShield card; Lakera summarization size; HarmBench size; other 2025-2026 injection sets.
- Toxic/off-topic sets for financial advice.
- FinanceBench second-annotator process.
- The page-reader leaves were not used; no leaf extracts exist to check quotes against.
- Labelling hours are my estimate, not sourced.
