# FinAdvisor research round 4: merged stage-1 evidence

Compiled 2026-11-02 from r4/ files (A-us, A-eu-uk, A-eval-sets, BC-prior-art, B-lifecycle, C-regions, D-guardrail, E-rag, G-gapfill) with skeptic verdicts S-skeptic-1 and S-skeptic-2 applied (skeptic overrides evidence file).
Compile-only: no new facts, no decisions. Read dates: 2026-11-01 or 2026-11-02 unless a cell says otherwise.
Tags: CORRECTED = skeptic changed the value; CONTRADICTED = evidence-file claim is wrong; UNSUPPORTED = not backed by a source the skeptic could read; UNVERIFIED = nobody read a primary source; [PREPRINT] = single unreviewed arXiv preprint (treat as hypothesis, not effect size).
Quote caveat: Google, Langfuse, Confluent, PostgreSQL, Notion, Presidio and NeMo quotes were relayed by a fetch summariser (two fetches agreed, not byte-verified). Raw reads: KMS pricing, Voyage docs, Anthropic docs, PyPI JSON, arXiv text, SEC/FINRA/EUR-Lex/FCA pages (skeptic 1).

---

## 0. Summary

Facts that change the design:
1. FCA Handbook: the evidence file's plan "crawl /handbook/COBS/ under OGL" is CONTRADICTED. Handbook T&C cl.35.3 bans any scraper/crawler/automated access except through the API (or written consent). The API is current/future versions only, rate-limited, and cl.13 lets FCA revoke access and require deletion of API data. UK point-in-time text therefore cannot be built lawfully without written FCA consent. fca.org.uk/legal cl.3.3 and the Handbook licence-agreement page also conflict with OGL (unresolved). https://handbook.fca.org.uk/footer-widget/terms-and-conditions
2. FINRA Rulebook is DROP: terms ban copying, bulk access, scraping, database build and ML/AI use. https://www.finra.org/terms-of-use (modified 2023-11-09). "SEC-hosted rule text" substitute is a legal question, not a licence.
3. No reuse licence was found for fund-company KIDs, 497K prospectuses or ADV brochures. Corpus must store a per-document licence/attribution field; ESMA reuse needs a transformed-text disclaimer in outputs.
4. Anthropic first-party API has no EU/UK residency: inference_geo is only "global" or "us" (1.1x price for us); workspace geo "us" only. Voyage, Identity Platform, Claude-on-Vertex-EU residency are UNVERIFIED. A UK/EU residency promise has no verified LLM path.
5. Erasure is a max of per-system windows, none measured end to end: BigQuery 9-14 days after DELETE, GCS soft delete 7 d (0 disables), Cloud SQL = longest backup retention you set, Kafka Basic >= 7 d + cleaner + tombstone, Langfuse ~15 min typical. PG18 temporal FKs cannot cascade.
6. EDGAR companyfacts returns 404 for fund trusts; fund risk/return facts must come from the quarterly RR datasets.
7. Public eval sets: no human-verified US/EU/UK advisor-regulation QA set exists; FinanceBench, FinDER, FinTextQA, EU2UK are NC. Own golden set 150-300 items (about 32-78 h, estimate); +/- 3.4 to 6.4 pp at 95%.
8. Temporal retrieval: hard validity filter beat current-version-only in the only study [PREPRINT FiscalQA Pro]; magnitude not transferable (all-model-hard questions, query carries a date).
9. Contextual retrieval: Anthropic 35/49/67% CONFIRMED but baseline is dense-only; independent off-domain preprint says a free section prefix + strong retriever roughly equals LLM enrichment. Voyage ships voyage-context-4 (document-aware embeddings, no LLM call): add as an ablation arm (E6 CONTRADICTED the "not available" note).
10. Guardrails: Model Armor free tier is 2M tokens/month (about 8 MB text); the ~10 MB demo corpus alone exceeds it (cost trivial, $0.10/M). Quota 1,200 QPM per project, shared. Latency, SLA, precision/recall NOT FOUND. 500 ms fail-closed timeout has no vendor basis. Prompt Guard 2 recall is on Meta's private English benchmark; licence Llama 4 community, manually gated.
11. Anthropic and Voyage limits are documented ceilings only; reranker: Voyage now lists rerank-3 as current and rerank-2.5 as "older"; ADR names rerank-2.5-lite.

Open items for Keshav:
- Ask FCA (Handbookfeedback@fca.org.uk) for written consent / Handbook licence agreement, or drop UK Handbook text from the first set.
- Legal view on fund-company and adviser documents (KID, 497K, ADV) and on SEC-hosted FINRA text.
- Decide residency promise wording given no EU/UK LLM path; test Claude on Vertex EU endpoint and ask Voyage (contact@voyageai.com) about regions.
- Run a 5-minute Identity Platform test: same email in two tenants.
- Pick the reranker to pin and ablate (rerank-3-lite vs rerank-2.5-lite).
- Decide erasure SLA wording (days, not instant) and whether per-subject KMS keys are wanted.
- Read the Anthropic prompt-injection chart before any ADR cites 13.8->1.9 / 8.0->1.4.

---

## 1. Track A: sources and eval sets

### 1.1 US sources

| source | licence/terms | access + rate limit | size | update freq | history/versions | formats | languages | change/delete detection | verdict |
|---|---|---|---|---|---|---|---|---|---|
| eCFR (17 CFR 275, 270, 279) | US gov publication; explicit terms page UNVERIFIED (docs page behind bot check); site is "unofficial" compilation (UNVERIFIED) | REST, no key, must send Accept-Encoding gzip (else 406); rate limit UNVERIFIED (use <= 1-2 rps) https://www.ecfr.gov/api/versioner/v1 | Pt 275 = 222,985 chars (225 KB XML, 39 sections); Pt 270 = 784,294; Pt 279 = 6,032; Title 17 = 17,320,268 chars. govinfo bulk ECFR-title17.xml = 17,369,932 B (CORRECTED from "4.69 MB", partial read) | titles.json up_to_date_as_of 2026-10-29 vs today 2026-11-02 (lag days) | versions/title-17.json?part=275: 143 records, 48 section ids, 9 removed, amendment_date 2016-12-31..2025-03-12 (reproduced by skeptic); point-in-time via /full/{date}/ | XML (full), JSON (structure, versions, search) | English | poll titles.json, diff versions on (identifier, amendment_date, issue_date); removed:true = tombstone; substantive:false = editorial | USE (best source, point-in-time native) |
| FINRA Rulebook | forbids copy, bulk, scraping, database build, ML/AI use; permission needed https://www.finra.org/terms-of-use (modified 2023-11-09; CONFIRMED raw) | no API/bulk found (UNVERIFIED that none exists) | not measured | Updates page, no feed found | n/a | HTML | English | n/a | DROP (ask FINRA in writing, or exclude) |
| EDGAR 497K / 485BPOS / N-1A | sec.gov "public information ... may be copied or further distributed"; "does not allow unclassified bots"; third-party text inside filings NOT covered https://www.sec.gov/about/privacy-information (reviewed 2023-11-29) | 10 req/s max, declared User-Agent required https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data (reviewed 2024-06-26, CONFIRMED) | Vanguard Index Funds sample: 497K median 106 KB HTML; 363 497K + 65 497 in 1,000 recent rows; 485BPOS up to 75 MB; Q3-2026 counts 497K 4,581, NPORT-P 13,950 | daily-index; full-index rebuilt weekly Saturday; annual refresh per fund | every filing immutable; point-in-time = filing date; amendments are separate forms | HTML, SGML | English | per-CIK submissions JSON (new accession, acceptanceDateTime) + daily-index; weekly reconcile vs full-index to catch removals; no per-filing tombstone seen | USE (publisher reuse of fund text unlicensed: see 1.4) |
| EDGAR XBRL companyfacts/frames | same as above | data.sec.gov, no CORS; same 10 rps | companyfacts.zip 1,414,913,699 B; submissions.zip 1,572,128,284 B (HEAD 2026-11-02, CONFIRMED) | nightly ~3 am ET | current facts only | JSON, zip | English | n/a | DROP for fund RR data: companyfacts 404 NoSuchKey for CIK 36405 (CONFIRMED, Apple control 200). CORRECTED: frames for dei return 200 with a valid concept, so the earlier "frames 404" probe is unreliable; conclusion (use RR datasets) stands |
| SEC Risk/Return summary datasets | as SEC | quarterly zip https://www.sec.gov/data-research/sec-markets-data/mutual-fund-prospectus-riskreturn-summary-data-sets (reviewed 2026-06-30) | 97 KB (2010Q4) to ~78 MB (2026Q2; 81,661,882 B) | quarterly ("updated quarterly"); lag ~2 weeks | Dec 2010 - Jun 2026 | zip of text+numeric | English | new quarter file; SEC: "cannot guarantee accuracy" | USE-WITH-CONDITION (optional structured cross-check; not a substitute for filings) |
| IAPD Form ADV Part 2A brochures | SEC page has no terms and says nothing on brochure copyright; IAPD terms UNVERIFIED | monthly SEC zips (2024: 385-663 MB each, ~11-12 GB/yr); per-firm PDFs on IAPD (URL pattern undocumented, JS site) https://www.sec.gov/foia-services/frequently-requested-documents/form-adv-data (reviewed 2025-12-16) | ~15-16k advisers (estimate); one probe PDF 8.1 MB (possibly Part 1+2) | monthly (Data.gov says quarterly; conflict UNVERIFIED) | archive 2007-2019 zips | PDF; Part 1 CSV | English | new monthly zip + mapping CSV; ADV-W CSV for withdrawals (columns not inspected) | USE-WITH-CONDITION (10-20 brochures for demo only; no reuse licence found) |
| EDGAR full-text search | n/a | efts endpoint returned 403 (not bypassed); no official API doc | n/a | n/a | n/a | n/a | n/a | n/a | DROP (build on submissions + daily-index) |

### 1.2 EU sources

| source | licence/terms | access + rate limit | size | update freq | history/versions | formats | languages | change/delete detection | verdict |
|---|---|---|---|---|---|---|---|---|---|
| EUR-Lex / CELLAR (MiFID II, MiFIR, PRIIPs Reg, Del. Reg 2017/565, RTS 2017/653) | reuse commercial and non-commercial per Decision 2011/833/EU; consolidated texts CC BY 4.0 (attribution, indicate changes); only the OJ is authentic; IAS may have special terms https://eur-lex.europa.eu/content/legal-notice/legal-notice.html (CONFIRMED) | CELLAR REST + SPARQL (https://publications.europa.eu/webapi/rdf/sparql) no registration; rate limits undocumented (UNVERIFIED, throttle). SOAP: registration, search only, results cap 10,000 from 2026-01-01 (CONFIRMED) | consolidated MiFID II XHTML ~1 MB per language (EN 956,709 B, DE 1,005,431, FR 1,044,217); PRIIPs Reg Formex 115 KB; five acts x versions ~40 MB in one language (estimate) | per-amendment new consolidated CELEX | CORRECTED: MiFID II 02014L0065 = 14, MiFIR 02014R0600 = 11, PRIIPs 02014R1286 = 5, 2017/565 = 6, RTS 2017/653 = 7 (not 6), total 43 (not 42); latest RTS pick 02017R0653-20230101 still valid (SPARQL, 2026-11-02) | XHTML, Formex 4, RDF; text/html and pdf 404 for consolidated CELEX | 23-24 per act (probe: 32014L0065 = 23, 32014R1286 = 24) | SPARQL poll of cdm:lastModificationDate; RSS (millions/day, registration UNVERIFIED); in-force and date_end-of-validity in graph; repeals via cdm properties; corrigenda are separate CELEX 3YYYYXNNNNR(nn) | USE (label consolidated text "not authentic"; carry base-act CELEX) |
| EUR-Lex Data Dump | EU Login account needed | bulk of acts in force by language (CELEX sector 3) | size UNVERIFIED | n/a | in-force only | n/a | per language | n/a | DROP (CELLAR REST suffices) |
| ESMA Library (Q&As, guidelines) | reproduction authorised with source acknowledgement; transformed text needs "drafted using material downloaded from ESMA's website" + non-endorsement; "free from ESMA" if sold; legislative text excluded https://www.esma.europa.eu/about-esma/legal-notice-and-data-protection (CONFIRMED) | no numeric rate limit found; Q&A tool bulk/API UNVERIFIED | MiFID II investor-protection Q&A PDF ~18 sections, frozen 2023-12-15 (ESMA35-43-349) | Q&A tool items dated (e.g. ESMA_QA_2952, 2026-10-20); news "New Q&As available" | JC PRIIPs Q&A same URL, new content (2022-12-21, 2024, JC 2023 22 dated 2025-12-05); deletions documented ("Overview of changes ... Prospectus Q&As" 2026-09) | PDF, HTML tool | English (others not checked) | news items + Q&A tool; RSS URL UNVERIFIED | USE-WITH-CONDITION (output must carry disclaimer) |
| PRIIPs KIDs (DWS Xtrackers, iShares, DB) | manufacturer documents, no open licence on any page read; DWS robots.txt disallows only /etfdata/* and /export/*; site terms UNVERIFIED | per-ISIN PDFs; DWS DE URL worked (100,190 B), EN/FR pattern 404 | ~100 KB per KID | annual-ish; KID states "accurate as at" date | no central database (ESA advice); reform: Council/Parliament deal 2025-12-18, OJ publication expected by Jan 2027, template likely to change | PDF | EN, DE, FR per fund | none (no feed) | USE-WITH-CONDITION (internal test/demo only until counsel or manufacturer agrees; tag KID with regime date) |

### 1.3 UK sources

| source | licence/terms | access + rate limit | size | update freq | history/versions | formats | languages | change/delete detection | verdict |
|---|---|---|---|---|---|---|---|---|---|
| legislation.gov.uk (onshored eur/2014/1286, eur/2017/565, eur/2017/653, uksi/2017/701) | OGL v3.0; EU-origin content dual-licensed under Decision 2011/833/EU; some Westlaw-derived attribution https://legislation.github.io/data-documentation/reuse-licence.html | API + crawling encouraged; user agent mandatory; CONFIRMED conflict: fair-use policy 1,500 requests / 5 min "per user" vs docs 3,000 / 5 min per IP; use 1,500; 403 on breach; no bulk dump | eur/2014/1286 53 KB; 2017/565 136 KB; 2017/653 194 KB; MiFIR 656 KB (probes) | publication log feed | point-in-time URLs /eur/2014/600/2018-01-03/data.xml; hasVersion list (PRIIPs 12, 2017/653 8, 2017/565 17); "applied/unapplied" effects lag 4-8 weeks (secondary summary) | CLML XML, HTML, PDF some, RDF | English; some Welsh (unchecked) | /update/data.feed (Publication Log), /new/data.feed, /changes/affected/..., dc:modified; titles "(revoked)" for UK PRIIPs Reg, 2017/565, 2017/653 (12 hasVersion links CONFIRMED); reason/date of revocation not read | USE |
| FCA Handbook (handbook.fca.org.uk) | T&C cl.25 OGL v3.0 + (c) FCA credit; cl.23 mixed provenance; CORRECTED/CONTRADICTED: cl.35.3 bars scrapers/crawlers/bots/automated access "other than by access to the API Data through the API"; fca.org.uk/legal cl.3.3 "must not reproduce or store any part of this site ... without prior written permission" (same page says Handbook under OGL); licence-agreement page says reproducing Handbook needs a Handbook licence agreement (2026-08-17); conflict unresolved | API (free account, login): current and future versions only, past dates return an error; "rate-limited per authenticated user and endpoint path" (no number); cl.13 revoke and "immediately delete all copies"; cl.19 Derived Data owned by user. API launched 2026-06-08 per FCA blog (date WEAK, not re-read) | COBS size not measured | Board meets >= 10x/year; monthly mailing list; "Last modified" column | website timeline gives past dates (from 2001) but cannot be crawled; API cannot supply history | HTML, PDF archive 2001-2004, API JSON (format not seen) | English (inference) | monthly email, Last-modified column; no RSS/XML | USE-WITH-CONDITION (API only, current text, revocable, delete duty) or DROP until FCA consent |
| FCA Financial Services Register API | data terms not read | free key; "BETA"; 50 requests per 10 s; no premium tier or limit raise (register-extract-handbook.pdf, April 2026, CONFIRMED); no SLA; one entity per query | n/a | n/a | n/a | JSON | English | n/a | DROP for RAG (entity metadata only) |
| FCA non-Handbook pages (policy statements, Handbook Notices) | restrictive cl.3.3 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | DROP until permission clear |

### 1.4 Recommended first set (smallest set covering 3 jurisdictions, updates, deletes, tables, >1 language)

Compiled from A-us section 5 and A-eu-uk subset, with skeptic changes applied.
- US: 17 CFR 275 (whole part, 39 sections, 225 KB XML) plus 143 version records (updates, point-in-time, 9 removed sections = deletes); a few Pt 270 rules optional; 3 fund families x 10-15 497K (~5 MB total); avoid 485BPOS (up to 75 MB). Optional 2026q2_rr1.zip (82 MB) for structured cross-check.
- EU: PRIIPs Reg 1286/2014 consolidated versions 20141229, one mid version, 20240109, each EN+DE+FR XHTML (9 files, ~0.5-1 MB each); one corrigendum (e.g. 32014R1286R(01)); RTS 2017/653 (02017R0653-20230101) for annex tables; MiFID II EN+DE 2 versions optional.
- UK: legislation.gov.uk eur/2014/1286 marked "(revoked)", 3 of its 12 point-in-time versions (delete case, lawful under OGL). FCA Handbook (COBS 9A, COBS 6) is NOT in the lawful first set unless FCA gives written consent or the API is accepted (current text only, revocable, delete duty).
- Withdrawals: JC PRIIPs Q&A 2022-12-21 vs 2025-12-05 snapshots (documented revised/deleted answers); ESMA Prospectus Q&A "Deleted" overview; ESMA investor-protection Q&A PDF frozen 2023-12-15 vs Q&A tool items from 2024.
- Tables: RTS 2017/653 annexes, 2-3 KIDs (iShares EN+DE for one fund, DWS DE) for cost tables; table extraction not run.
- Languages: EN+DE+FR via CELLAR.
- Notes on dropped or restricted items:
  - FINRA: DROP (terms above). SEC-hosted rule-filing text under "may be copied" is INFERENCE only: the SEC page does not address third-party copyright (legal question).
  - FCA Handbook: crawl forbidden (cl.35.3); API current-only and revocable; no point-in-time via API.
  - Publisher documents (KIDs, 497K, ADV brochures): no reuse licence found; "public" is not "licensed"; multi-tenant product that stores and quotes them is the exposure. Demo/internal only.
  - ESMA output disclaimer for transformed text is not in any design (skeptic hidden assumption 4).
- Change-detection test plan: CELLAR lastModificationDate poll (5 acts); legislation.gov.uk /update feed filtered on three eur items; eCFR versions diff; EDGAR per-CIK submissions + weekly full-index reconcile; ESMA news + Q&A tool; FCA monthly email (manual).
- Corpus must store per-document licence and attribution (CC BY 4.0, OGL v3.0 with (c) FCA, ESMA transformed-text disclaimer, KID = unknown) and flag consolidated EU text "not authentic".

### 1.5 Eval sets: QA benchmarks (licence per set)

| set | licence (data) | commercial | size | docs | fit |
|---|---|---|---|---|---|
| FinanceBench | CC-BY-NC-4.0 (HF API, modified 2024-11-17, CONFIRMED) | no | 150 open of 10,231 | PDFs in GitHub repo | low (10-K) |
| FinQA | CC-BY-4.0 (HF); MIT (GitHub) | yes | 8,281 | excerpts | low |
| TAT-QA | CC-BY-4.0 (HF); MIT (GitHub) | yes | 16,552 Q | context | low |
| ConvFinQA | MIT (GitHub) | yes | 3,892 conv / 14,115 Q | context | low |
| DocFinQA | MIT (HF) | yes | 7,437 Q | full filings (avg 123k words) | low; long-document stress |
| FinDER | CC-BY-NC-4.0 | no | 5,703 | evidence passages | low-medium |
| FinTextQA | CC-BY-NC-SA-4.0 | no | 1,262 | not verified | medium |
| SEC-QA | data licence UNVERIFIED, no repo found | UNVERIFIED | framework | n/a | low |
| FinanceRAG (ICAIF 24) | Kaggle terms UNVERIFIED; repackages NC sets | UNVERIFIED | 7 subsets | n/a | low |
| ObliQA | Apache-2.0 (HF, 2026-02-24, CONFIRMED) | yes | 27,869 synthetic | 40 ADGM docs (UAE law) | high topically, tests none of US/EU/UK |
| ObliQA-MP | Apache-2.0 | yes | 2,976 (LLM labels, not expert) | same | high |
| ObliQA-XRef | "other" (2026-05-09), terms unread; must respect ADGM and UK PRA Rulebook terms | UNVERIFIED | 17,394 | passages in rows | high (UK PRA), synthetic gold |
| EU2UK / UK2EU RegIR | CC-BY-NC-SA-4.0 | no | 1,700 + 1,800 queries | yes | medium; retrieval only |
| FinBen en-regulations | MIT, gated | yes | 254 test | in row | medium |
| LegalBench-RAG | repo MIT; per-subset terms (ContractNLI, CUAD, MAUD, PrivacyQA) | mixed | 6,858 Q (mini 776) | download | low; snippet-level ground truth method |
| MultiFinBen PolyFiQA-Expert | MIT vs Apache-2.0 (card conflict) | yes | 76 | in row | low; no FR/DE/IT |

Finding: no public human-verified QA set covers US, EU or UK advisor regulation. ObliQA cards say they are not expert annotation.

### 1.6 Golden-set plan

- Method sources: Ragas test generation (candidates only, no stated human review, no size recommendation); ARES "a few hundred human annotations" with PPI https://arxiv.org/abs/2311.09476 (abstract); FinanceBench protocol (analyst templates, evidence string + page number); LegalBench-RAG snippet ground truth. Miller https://arxiv.org/abs/2411.00640 (SE_Bernoulli, paired analysis, clustered SE for questions from the same document).
- Plan: 40-60 real documents across US/EU/UK; LLM candidate generation (Ragas-style single/multi-hop + persona queries) + hand-written compliance cases; human-check every item (question realistic, evidence span located, gold correct, answerable or not); store evidence span and source hash; include unanswerable, cross-jurisdiction, conflicting-source and injection-in-document items (no public set covers them); ObliQA only as external retrieval smoke test.
- CI arithmetic (CONFIRMED by skeptic recompute, 1.96*sqrt(p(1-p)/n)):

| n | half-width p=0.90 | half-width p=0.80 |
|---|---|---|
| 150 | +/- 4.8 pp | +/- 6.4 pp |
| 200 | +/- 4.2 pp | +/- 5.5 pp |
| 300 | +/- 3.4 pp | +/- 4.5 pp |

  Rule of three: 0 failures in 150 gives upper bound 2%; in 300 gives 1%. "About 250 per arm for a 10 pp gap" depends on baseline (about 200 at 0.8 vs 0.9; about 290 at 0.7 vs 0.8); 5 pp gap about 1,000 per arm unpaired; paired needs fewer. These formulas are the author's arithmetic on Miller eq. 2-3, not quoted from the paper.
- Clustering caveat: items from one document are not independent; real interval is wider. Slices below ~30 items are directional only.
- evalstats [PREPRINT] arXiv 2609.35815 (Arawjo, 2026-09-20): "We strongly advise against bootstrap CIs at N<100"; bootstrap CIs overconfident nearly everywhere; on paired binary data none reached nominal coverage even at N=100; Bonett-Price for paired binary; Romano-Wolf only at n>=30; judge needs rho^2 >= 0.4, below 0.2 unusable. Skeptic: at N=150-300 clustered by document, effective N can fall below 100, so the N<100 warning may still apply; E's paired-bootstrap-over-clusters protocol is in tension with it.
- Labelling hours (ESTIMATE, no source; one non-lawyer labeller, 8-12 min per item, 30-40% candidate discard, no inter-annotator agreement):

| checked items | labelling h | overhead h | total h |
|---|---|---|---|
| 150 | 20-30 | 12-16 | 32-46 |
| 200 | 27-40 | 12-16 | 39-56 |
| 300 | 40-60 | 14-18 | 54-78 |

  Add 20-40% for unfamiliar regulation; second reviewer on 10-15% sample if available.

### 1.7 PII, direct injection, indirect injection sets

| set | licence | size | languages / labels | note |
|---|---|---|---|---|
| ai4privacy openpii-1.5m | CC-BY-4.0 per card text (HF metadata "other", license_name cc-by-4.0; card governs, CONFIRMED) | 1,636,375 | 30 languages, 19 classes | synthetic; no IBAN / account number classes |
| ai4privacy openpii-1m | same metadata | ~1.4M | 23 | |
| ai4privacy pii-masking-200k | CORRECTED: HF metadata has NO licence field (file said "other") | 100K-1M | en, fr, de, it | do not use until terms read |
| ai4privacy 300k / 400k | "other", license.md unretrievable; card: commercial entities contact licensing@ai4privacy.com | 100K-1M | 6 languages; FinPII-80k extended classes need licence | exclude |
| Gretel synthetic_pii_finance_multilingual | Apache-2.0 (HF 2024-06-11); card body not re-read | 55,940 | en, fr, de, nl, es, it; 29 PII types, 100 formats | LLM-labelled, GLiNER-checked: label noise possible |
| deepset/prompt-injections | top-level apache-2.0 and nested cc-by-4.0 in same README (conflict real) | 662 (116 test) | languages UNVERIFIED | smoke test only |
| Lakera gandalf_ignore_instructions | MIT (publisher claim; prompts from public players, July 2023) | 1,000 | en | one attack family |
| Lakera mosscap_prompt_injection | MIT | 100K-1M | en | unfiltered, needs cleaning |
| JailbreakBench / HarmBench | MIT / MIT gated | 200 / <1K | en | harm behaviours, low relevance; JBB benign set helps over-refusal |
| Qualifire prompt-injections-benchmark | CC-BY-NC-4.0 gated | 5,000 | n/s | exclude |
| PromptShield | Apache-2.0 per API, card not read | n/r | en | UNVERIFIED |
| PINT | repo MIT; data file not found public | 4,314 described | many | use format only |
| BIPIA | MIT text; NOASSERTION in API; Web/Summarization contexts must be downloaded under source terms | 5 tasks | en | patterns only, not contexts |
| InjecAgent | MIT | 1,054 | en | tool agents, not document RAG |
| AgentDojo | MIT | 97 tasks / 629 cases | en | environment, heavy to adapt |
| LLMail-Inject | MIT (HF 2025-05-16, CONFIRMED) | 208,095 attacks | en | closest to retrieval-poisoned docs; wrap strings into financial chunks yourself |

Recommended public-demo picks (A-eval): QA smoke ObliQA/ObliQA-MP; PII openpii-1.5m + Gretel; direct Lakera gandalf + deepset; indirect LLMail-Inject. Excluded: FinanceBench, FinDER, FinTextQA, Qualifire, EU2UK/UK2EU, ai4privacy 200k/300k/400k, PINT data. Toxic/off-topic sets for financial advice: not researched (gap). Re-run the licence check on the exact dataset revision at integration and record it.

---

## 2. Track B: data engineering

### 2.1 Change capture per source

| source | change feed | delete signal | gap / backstop |
|---|---|---|---|
| eCFR | titles.json up_to_date_as_of; versions/ diff | removed:true | rate limit UNVERIFIED |
| EDGAR | per-CIK submissions JSON, daily-index | corrections/removals only in weekly Saturday full-index rebuild | weekly reconcile |
| CELLAR | SPARQL lastModificationDate poll; RSS | in-force flag, end-of-validity, repeals properties | CELLAR rate limits undocumented |
| legislation.gov.uk | /update (Publication Log) and /new feeds | "(revoked)" title, Repealed status | 1,500 / 5 min |
| ESMA | news + Q&A tool | "Deleted" column in changes overview | RSS URL UNVERIFIED |
| FCA Handbook | monthly email, Last modified | n/a | API current-only |

Prior art (BC): Google Drive Changes API (opaque token, store with the ingest transaction, push = "poll now"); Airbyte incremental (cursor misses hard deletes and silent edits, so full-listing diff backstop plus overlap window); Notion Page State: re-chunk/re-embed/re-upload all spans on any change; fix = two 64-bit xxHash per span (text, metadata) in DynamoDB, metadata-only change = cheaper PATCH, "70% reduction in data volume" (verified against Notion blog 2026-02-19, CONFIRMED). Notion's 60% search-spend, 35% EMR and p50 70-100 -> 50-70 ms belong to the turbopuffer migration, NOT to hash dedupe. gend.co "10x / 90% cost" UNSUPPORTED. legislation.gov.uk "applied/unapplied" effects: model "known change, not yet applied" as a state (secondary summary only).

### 2.2 Versioning

- PG18 temporal (https://www.postgresql.org/docs/18/sql-createtable.html, CONFIRMED): PRIMARY KEY/UNIQUE `( ..., col WITHOUT OVERLAPS )`, column must be range or multirange, empty ranges not permitted, GiST index; non-range key columns (uuid/int/text) need btree_gist. FK `[, PERIOD col]`, referenced table needs WITHOUT OVERLAPS key. RESTRICT, CASCADE, SET NULL, SET DEFAULT each "not supported" in a temporal FK (NO ACTION: page silent). Consequence: tenant/document delete cannot cascade through a temporal FK; delete children explicitly in order.
- Cloud SQL: PG18 is default, 18.6, regular support from 2025-09-25 (CONFIRMED); pgvector 0.8.5 on PG13+; btree_gist 1.8 on PG18 (extensions page). Pgvector README is at 0.8.7 (G), so Cloud SQL lags two patch releases (UNCHECKED; features of 0.8.6/0.8.7 unavailable).
- pgvector iterative scan (README, 2026-11-02): "Starting with 0.8.0 ... iterative index scans"; hnsw.iterative_scan = strict_order | relaxed_order; ivfflat.iterative_scan = relaxed_order; hnsw.max_scan_tuples default 20,000; hnsw.scan_mem_multiplier default 1; ivfflat uses ivfflat.max_probes (no max_scan_tuples). No guarantee of LIMIT-many results or full recall. Behaviour under RLS and LIST partitions NOT answered.
- Bitemporal prior art: XTDB (valid time + system time, non-destructive, conflicts with erasure; not adoptable at demo budget); legislation.gov.uk point-in-time per provision (commencement differs per section), so chunk identity = (doc_id, provision path, valid range). No production write-up found for bitemporal chunks + vector index; answer cache key would need as_of and corpus version (inference).
- dbt: model contracts (enforced: true preflight; table supported, views names/types only; Python/materialized view/ephemeral/sources/seeds/snapshots not supported); model versions (latest = numerically greatest, deprecation_date from 1.6); unit tests from 1.8, SQL models only. Contract tab mapping (Postgres enforces all five constraints) is reader-inferred, verify per adapter.
- Pandera 0.35.0 (2026-10-25): CORRECTED polars floor is `polars>=1.20.0` (PyPI extra), not the docs' ">= 1.0.0". LazyFrame validates schema only by default (data-level needs collect() or PANDERA_VALIDATION_DEPTH=SCHEMA_AND_DATA). dagster-pandera 0.29.28 pins dagster==1.13.28, pandas<3.0.0, pandera>=0.24.0.
- Dagster 1.13.28 (PyPI 2026-10-30): blocking asset checks (blocking=True) stop downstream within a run; docs frame it as in-run, cross-run/schedule/partition behaviour not stated (B's "in-run only" is an inference from silence: test before using as PII gate). Single-run backfills; sensor run_key dedupe and cursors. CORRECTED dagster-openlineage 0.2.1 (2026-05-22): no release in five months while dagster shipped weekly, 0.x, "OpenLineageEventListener removed", default changes in v0.3; pin it and do not make lineage a gate. Declarative Automation documented, not beta.
- Lineage/quality prior art: Airbnb reconciliation framework [OLD, ~2020, not read directly, partial match]; Uber Hudi post (2026-01-16) is silent on deletes; OpenLineage/dbt write-ups, Fivetran, Great Expectations: NOT covered.

### 2.3 Deletion per store (windows)

| store | delete mechanism | window | crypto-shred option | proof |
|---|---|---|---|---|
| Cloud SQL (OLTP + pgvector) | physical DELETE (children first; no temporal-FK cascade) | live rows immediate; backups: automated retention 1 day to 10 years (your setting), on-demand "indefinitely until manually deleted", deleted-instance backups 4 days then removed one per day; PITR log retention days NOT found; no per-row purge from backups | per-tenant/subject CMEK/KMS key: destroyed key version makes enhanced backups "permanently unrestorable"; standard backups, replicas, PITR not documented; disabled key suspends instance | none documented; test restore in scratch instance after key destruction. SLA ceiling = longest configured backup retention, not "4 days" |
| BigQuery | DML DELETE; 2 concurrent + 20 queued mutating DML per table; avoid DML on rows streamed in last 30 min; fine-grained DML tables cannot drop single partitions | time travel 2-7 days (default 7) + fail-safe 7 days not configurable and not queryable: 9 to 14 days post-DELETE | AEAD keyset wrapped by KMS key in same region; destroying key = design inference, no doc describes it; test decrypt-fails | none documented |
| GCS | object delete by generation; lifecycle for noncurrent versions (async, no timing guarantee) | soft delete default 7 d, range 7-90 d, 0 disables; cannot purge early; retention lock irreversible (do not use on subject-data buckets) | KMS CMEK effect of key destruction not found | none documented |
| Kafka (Confluent Basic) | tombstone + compaction; Basic supports compacted topics (5 TB per partition, 1,500 compactable partitions, CONFIRMED) | max.compaction.lag.ms minimum 7 days on Basic/Standard/Enterprise (6 h Dedicated), editable; delete.retention.ms default 1 d, max 60,566,400,000 ms (701 d); erasure latency >= 7 d + cleaner scheduling + tombstone retention; retention.ms max on Basic NOT FOUND; cluster-level settings not editable on Basic | client-side field-level encryption (Stream Governance Advanced, Google KMS KEKs, DEK Registry 10,000 DEKs); losing KEK makes DEKs inaccessible (docs never say "crypto-shredding") | none |
| Schema Registry | soft delete then ?permanent=true; "removes all metadata, including schema IDs" | immediate after hard delete; soft-deleted IDs still count toward limit | n/a | n/a |
| Langfuse | DELETE /api/public/traces/{id} or batch (cascades to scores, observations); sessions have no delete endpoint (look up trace IDs, then batch) | "usually within 15 minutes" (typical, not a guarantee; no confirmation returned); project delete can take days; deletion rate-limited (no number) | n/a | re-query to verify; dataset items and audit logs survive retention, and whether per-trace delete removes dataset items copied from traces is NOT stated |
| Langfuse retention | Pro ($199) / Enterprise only, min 3 days, nightly; Hobby and Core "Not available" | n/a | n/a | n/a |
| Cloud Logging | no per-entry delete documented; CORRECTED: projects.logs.delete removes all entries of a log in the _Default bucket only (coarse, tenant-wide, log reappears on new entries); bucket delete | default retention 30 d; custom 1-3650 d; _Required 400 d fixed; bucket deletion delayed 7 days; CMEK key removal up to 1 h lag | n/a | keep PII out of logs (exclusion filters apply after receipt, do not reduce write quota) |
| Cloud KMS (shred mechanism) | scheduled destruction | default 30 d, set only at key creation, min 24 h (import-only 0), max 120 d | the mechanism itself; Google calls destroyed data "crypto-shredded" | key state; per-key cost below |

Hidden-assumption notes (S2): "erased within N days" is a max over systems and windows chain; no end-to-end erasure measured. Crypto-shredding assumes the data key is not cached or re-wrapped elsewhere. KMS price CONFIRMED: software key version $0.06/month ($0.000082192/h, Mar 17 2025), Enabled, Disabled and Scheduled-for-destruction versions bill, destroyed free, $0.03 per 10,000 ops, so per-subject key = $0.72/yr per key version. KMS quota: no cap on keys/versions; from 2026-02-16 read 600 TPM, write 100 TPM per project, token-based (per-operation token cost unchecked; key-creation bursts and DEK unwrap fan-out must be recomputed; raisable).
Prior art: Spotify Padlock 2018 (per-user keychain; 1M lookups/s, p99 < 15 ms, rejected per-service delete endpoints and tokenization; guarantee covers keychain deletion, not derived copies, logs or embeddings; CONFIRMED) [OLD]. Embeddings are not decryptable plaintext but encrypting vectors defeats pgvector search, so crypto-shredding covers GCS, Parquet, Kafka, backups; live index needs physical delete (BC inference). Iceberg/Hudi/LinkedIn/Segment erasure claims are secondary only: UNSUPPORTED, do not rest a design on them. No "proof of deletion" design found (Segment per-system receipts unverified).

### 2.4 Re-embedding
- Notion (2026-02-19): sharded by workspace ID; new "generation" when indexes fill; migration did full re-index, embeddings model upgrade, gradual cutover generation by generation with validation (CONFIRMED).
- Practitioner pattern (Tian Pan 2026-07-05, single-author blog; its cost example is the author's own): build new index beside old, dual writes, backfill without overwriting fresher vectors, alias flip, golden-query recall@k gate, keep old index for rollback; handle hard deletes mid-migration. Uber/Pinterest blue-green claim UNVERIFIED.
- Design inputs: per-vector model_id; apply erasure to both versions during overlap; per-tenant cutover with LIST partition per tenant (BC inference).
- Notion sharding post (2021) migration framework: double-write, backfill, verify, switch; skip older versions on backfill [OLD].

### 2.5 Scale envelope (Anthropic, Voyage)

Anthropic (https://platform.claude.com/docs/en/api/rate-limits, raw, CONFIRMED). Tiers are now Start / Build / Scale / Custom plus an "Evaluation" tier with lower limits for new orgs.

| model | Start RPM / ITPM / OTPM | Build | Scale |
|---|---|---|---|
| Sonnet 5.5 | 4,000 / 2,000,000 / 400,000 | 10,000 / 5,000,000 / 1,000,000 | 13,000 / 10,000,000 / 2,000,000 |
| Haiku 5.5 | identical to Sonnet 5.5 at every tier | | |
| Sonnet 5 / Haiku 4.5 | 1,000 / 2M / 400K | 5,000 / 5M / 1M | 10,000 / 10M / 2M |

- Spend caps per month: Start $500, Build $1,000, Scale $200,000; at cap requests return 429 "enforced_spend_limit_reached" with no retry-after until the 1st (UTC).
- cache_read_input_tokens do not count toward ITPM for most models; cache_creation tokens do (cold-cache bulk contextualization is charged at creation tokens). max_tokens does not factor into OTPM. Acceleration limits can 429 on sharp growth.
- Message Batches: 100,000 requests or 256 MB per batch; Start 1,000 RPM / 200,000 queued, Build 2,000 / 300,000, Scale 4,000 / 500,000; 24 h expiry; results 29 days; 50% price; caching stacks (best-effort 30-98% hits; 1-hour cache recommended). Batch/50%/24 h/29-day facts are UNCHECKED by skeptic; batch is ZDR not eligible per page metadata.
- Deprecation: "at least 60 days' notice" for public models; claude-sonnet-5-5 not sooner than 2027-09-28; claude-haiku-5-5 2027-10-07; claude-haiku-4-5-20251001 "not sooner than 2026-10-15" is past and still Active (60 days is a floor, not a schedule); sonnet-4-5 deprecated 2026-09-30, retires 2026-11-30 (61 days). Bedrock/Google set their own schedules. API version 2026-10-21 removed temperature/top_p/top_k (400 error): pinned-parameter code breaks.

Voyage (raw docs, CONFIRMED): base 2,000 RPM all models; TPM voyage-4 8M, voyage-4-large 3M, voyage-4-lite 16M, voyage-context-4 3M, rerank-2.5 / rerank-3 2M, rerank-2.5-lite / rerank-3-lite 4M; tier 2 needs >= $100 paid (2x), tier 3 >= $1,000 (3x), counted on "billed usage, excluding free tokens" so the 200M free tokens do not buy tier 2. Prices per 1M tokens: voyage-4 $0.06, voyage-4-large $0.12, voyage-4-lite $0.02, voyage-context-4 $0.12; rerank-3 $0.05, rerank-3-lite $0.02 (current table); rerank-2.5 $0.05 and rerank-2.5-lite $0.02 are in the "Older models" table (CORRECTED; page also contradicts itself on rerank free tokens); first 200M free for the voyage-4 family. Batch: 12-hour window (an example shows 8h), 33% discount, up to 100K inputs, no free credits on batch, <= 100 in-flight batch jobs / 1B tokens. Embeddings: context 32,000 tokens; list max 1,000; tokens per request 1M (lite), 320K (voyage-4), 120K (large). voyage-4 blog 2026-01-15: large beats voyage-4/lite/Gemini Embedding 001/Cohere v4/OpenAI v3 Large by 1.87/4.80/3.87/8.20/14.05% avg NDCG over 29 RTEB datasets (vendor benchmark). MIRACL/MMTEB multilingual numbers NOT FOUND; supported-language list not on embeddings page.

---

## 3. Track C: regions and logins

### 3.1 Per-service region facts and cross-region limits

| service | fact | limit / caveat | link |
|---|---|---|---|
| Cloud SQL | europe-west2 London, europe-west3 Frankfurt, us-central1 Iowa available | cross-region read replicas exist, async, manual promote; DR replica + switchover need Enterprise Plus; plain cross-region replica on Enterprise edition: page silent; shared-core tiers (db-f1-micro, db-g1-small) outside SLA, not for production | https://docs.cloud.google.com/sql/docs/postgres/locations, /replication/cross-region-replicas |
| BigQuery | dataset location fixed; cross-location queries and JOINs error | EU multi-region excludes London (europe-west2) and Zurich; multi-region has no regional redundancy; cross-region copy procedure not on page | https://docs.cloud.google.com/bigquery/docs/locations |
| GCS | region, dual-region, multi-region types | relocation possible with Storage Intelligence (so "location immutable" is not strictly true); London-Frankfurt predefined dual-region UNVERIFIED | https://docs.cloud.google.com/storage/docs/locations |
| Confluent Basic (GCP) | us-central1 and europe-west2: Basic/Standard/Enterprise/Dedicated; europe-west3: no Enterprise | cluster-link destination must be Dedicated or Enterprise (Basic/Standard may only be source of destination-initiated links); max 10 links per destination; Basic 1-50 eCKU, 250/750 MBps, 1,500 partitions, 99.5% SLA, no RBAC for Kafka resources; Enterprise ~$895/month | https://docs.confluent.io/cloud/current/multi-cloud/cluster-linking/index.html |
| Cloud Run + global external ALB | one serverless NEG per region behind one anycast IP; deploy per region | default routing is closest-region (latency), no automatic cross-region failover; tenant pinning needs URL map host/path routing or app redirect (header routing UNVERIFIED); min instances apply per region; up to 30 min for LB to serve; needs Premium tier | https://docs.cloud.google.com/run/docs/multiple-regions |
| Cloud Armor | global policies attach to global external ALB | one policy across backends in several regions and pricing not read (UNVERIFIED) | https://docs.cloud.google.com/armor/docs/security-policy-overview |
| Langfuse Cloud | US Oregon (AWS us-west-2), EU Ireland (eu-west-1), HIPAA Oregon, Japan | "All data, user accounts, and infrastructure are completely separated between the regions": no cross-region org; separate account per region | https://langfuse.com/security/data-regions |
| Anthropic API | inference_geo "global" (default) or "us"; workspace geo "us" only, fixed at creation | us-only 1.1x price; supported Claude 4.6+; rate limits shared across geos; on Bedrock/Google-managed Vertex region follows endpoint/profile; Claude on Vertex EU endpoints UNVERIFIED (CONFIRMED by skeptic: no EU/UK option on first-party API) | https://platform.claude.com/docs/en/build-with-claude/data-residency |
| Voyage | zero-day-retention opt-out exists | data location, regions, Marketplace/Vertex: docs silent, UNVERIFIED; vendor says contact | https://docs.voyageai.com/docs/faq |
| Model Armor | 16 regions + us/eu multi-regions (locations page, undated) | sanitize needs regional endpoints | https://docs.cloud.google.com/model-armor |

### 3.2 Identity Platform multi-tenant login

- Tenants are user silos: "unique silos of users and configurations within a single Identity Platform project"; each tenant has its own users and IdPs.
- Quota CONFIRMED: tenants per project "Instrumentless 2 / Billing instrument Unlimited" (updated 2026-10-26); no limit on IdPs per project or tenant. Billing-enabled project needed for more than 2 tenants.
- Tenant limits: no "Disabling account linking", no tenant-specific blocking function.
- Client: set tenantId on the auth instance to switch; tenantId is not persisted on reload (app must store it); currentUser does not change when tenantId is switched, so one auth instance per tenant for two simultaneous logins.
- Server: if tenant ID unknown, verify the token at project level first to extract the tenant, then tenant-aware verification; firebase.tenant mismatch raises auth/mismatching-tenant-id. Cross-region verification with same project keys follows from this but is not stated: UNVERIFIED.
- SAML per tenant confirmed; OIDC per tenant listed, setup detail UNVERIFIED; session cookies per tenant UNVERIFIED.
- UNVERIFIED: same email in two tenants (pages silent; needs a live test); Identity Platform data location (no page found; treat identity as global).
- Prior art for multi-region membership login: none found. WorkOS 2026-01-29: authentication control plane may stay global while content is in region; Slack also keeps some identity metadata global. Implied pattern (BC inference): global identity + global tenant directory (tenant to region) + token with tenant claim + router. Identity Platform per-tenant user pools mean one person in two tenants has two identities unless linked.

### 3.3 Second-region monthly cost delta (prices UNVERIFIED unless stated)

Assumptions: one identical cell, demo on demand, Cloud Run min instances 0, smallest non-HA Cloud SQL Enterprise instance. All GCP unit prices come from https://cloud.google.com/products/calculator; pricing pages returned truncated content.

| item | delta assumption | price |
|---|---|---|
| Cloud SQL smallest non-HA instance (second region) | always-on instance + storage; stop-when-idle behaviour UNVERIFIED | UNVERIFIED |
| Cloud SQL HA | "roughly doubles" instance cost; multiplier not read | UNVERIFIED |
| Cloud SQL cross-region DR replica | extra instance on Enterprise Plus | UNVERIFIED |
| Cloud Run min instances 0 | request-based; idle price with min>0 not read | UNVERIFIED |
| Confluent Basic cluster | "First eCKU free, then $0.14" per eCKU-hour; $0.05/GB in/out; $0.08/GB-month storage; "$0/Month" start (CONFIRMED by skeptic; pricing from summarised page) | $0 base at idle, plus data and storage |
| BigQuery dataset | empty dataset no fixed charge; storage and queries | UNVERIFIED |
| GCS bucket | storage + operations | UNVERIFIED |
| Global external ALB | second region adds a NEG and backend service, not a forwarding rule; per-rule/LCU pricing not read | UNVERIFIED |
| Cloud Armor | policy attaches to global backend; per-policy/rule fee not read | UNVERIFIED |
| Langfuse Cloud | separate account per region; plan price for second account not read (pricing page: Hobby 50k units, 30-day access; Core $29, 90 days; Pro $199; Enterprise $2,499; 3 years) | UNVERIFIED |
| Total delta | cannot be stated from verified docs | main driver Cloud SQL |

### 3.4 Prior art on cells and residency

- AWS cell-based architecture (2023-09-20, CONFIRMED): "If a workload uses 10 cells to service 100 requests ... 90% ... unaffected"; router "the thinnest possible layer"; partition mapping via cryptographic hash + modular arithmetic (hash-mod does not pin a region, so a directory lookup for residency is a deviation); partition key customer ID. CORRECTED: the "multi-Region usually not required" sentence is from the reliability-pillar bulkhead page and concerns HA, not residency. AWS best practices also say "Start with multiple cells from day one" and "Start with a cell migration mechanism from day one" (omitted from BC). "Allowing cells to grow without bounds" anti-pattern quote: UNSUPPORTED (anti-patterns page failed to load). Cells are a blast-radius pattern; applying to residency is an analogy.
- Atlassian data residency 2021 [OLD]: copy first, delete only after all copies finish; on failure re-online tenant then delete partial copies; largest tenants moved "in under 60 minutes" after sharding the index; p90 ~500 ms faster after moving EU customers; relies on a control plane serving millions of req/min. Page does not say tenants are offline during a move (later support doc says app goes offline; undated WebSearch).
- Slack: cells are AZs not residency units (2023-08-22); residency per customer in one region, some categories (member profiles, IDs) may sit outside it (help page undated).
- Salesforce Hyperforce: grids, cells and supercells under one control plane; org migration detail not retrieved. Stripe: nothing retrieved. Notion sharding posts are workspace-ID sharding, not residency [OLD].
- Design inputs (BC inference): region column on tenant row; thin tenant-to-region directory; copy then delete; check region at consume time (applies to outbox/acl-applier); decide which fields are global (user id, email, tenant membership) and state it in the privacy notice.

---

## 4. Track D: guardrails

### 4.1 Tool comparison

| tool | cost | latency stated | prompt (a) | ingest chunks (b) | output (c) | licence |
|---|---|---|---|---|---|---|
| Model Armor | free to 2M tokens/month, then $0.10 per 1M; SDP adds no charge | NOT FOUND (measure) | PI/jailbreak, malicious URL (first 256), SDP, RAI; CSAM always on | document screening PDF/CSV/TXT/DOCX/PPTX/XLSX, 4 MB cap, 1,200 QPM | sanitizeModelResponse, detect-only | managed |
| Presidio 2.2.366 (PyPI 2026-10-27) | CPU only | NOT FOUND | PII | PII | PII sentence-buffered | MIT; UNSUPPORTED (not rechecked by skeptic) |
| NeMo Guardrails 0.24.1 | CPU/LLM calls | jailbreak rail "2057 ms CPU / 115 ms GPU" | heavy | poor | partial | Apache-2.0; figures UNSUPPORTED (not rechecked) |
| Prompt Guard 2 86M / 22M | self-host | 92.4 / 19.3 ms on A100, 512 tokens (CONFIRMED); CPU NOT FOUND | yes | yes with 512-token windows | no | CORRECTED: HF license "other", license_name llama4, gated manual; Llama 4 Community License text not read; model card says backbones MIT |
| protectai deberta-v3 prompt-injection v2 | self-host | NOT FOUND | yes, no jailbreak | yes | no | Apache-2.0, archived |
| Granite Guardian 4.1 8B | GPU | NOT FOUND | harm/groundedness | heavy | yes | Apache-2.0 |
| Qwen3Guard-Gen-0.6B | small GPU/CPU? | NOT FOUND | harm, jailbreak, PII; 119 languages | meh | yes | Apache-2.0; UNSUPPORTED (not rechecked) |
| Llama Guard 4 / ShieldGemma-2b | GPU | NOT FOUND | harm only | no | harm only | "other" / Gemma |
| Anthropic Citations | output tokens only (cited_text excluded) | n/a | n/a | n/a | grounding spans; cannot combine with structured outputs (400); enable on all or none of documents | API |
| Spotlighting | $0 | ~0 | indirect | n/a | n/a | paper |

### 4.2 Measured numbers with caveats

- Model Armor (https://docs.cloud.google.com/model-armor/quotas, 2026-10-28; CONFIRMED): 1,200 QPM per project; token limits 65,536 (PI/jailbreak, RAI, CSAM), 130,000 (SDP, 0.5 MB); files 4 MB; over limit returns EXECUTION_SKIPPED. Skeptic additions: EXECUTION_SKIPPED also on modality mismatch; PI filter returns NO_MATCH_FOUND under three words; pricing token = 4 chars excluding whitespace; sanitize needs regional endpoints. SDP Basic = 6 US-centric infoTypes, inspect only; Advanced de-identify not supported for file prompts or streaming, so Model Armor cannot be the pseudonymizer. Latency, SLA, GA status per feature (images and exclusion rules Preview), published precision/recall: NOT FOUND. Quota is per project and shared by prompt, ingest and output checks (S1 hidden assumption 5). 500 ms fail-closed timeout has no vendor figure.
- Prompt Guard 2 (PurpleLlama MODEL_CARD, CONFIRMED): AUC .998 / .995, recall at 1% FPR 97.5% / 88.7%, A100, 512 tokens. Caveat: measured on a Meta PRIVATE benchmark (Prompt Guard 1 scores 21.2% recall on it), English; not portable to finance documents. A 100 KB 497K is about 25k tokens, so about 50 windows per document at ingest.
- Spotlighting arXiv 2403.14720 [PREPRINT] (Microsoft; June 2023 GPT-3.5, GPT-4, text-davinci-003, temperature 1.0; 1,000 synthetic documents, simple keyword payload; no Claude tested). CORRECTED reading: baseline ASR around 60% (abstract ">50%"); delimiting only about halves ASR and authors "do not recommend" it; datamarking summarisation GPT-3.5 about 50% to below 3% (text says approx, caption 3.10%, internal inconsistency), text-003 40% to 0.00%, datamarking Q&A GPT-3.5 8.0%, GPT-4 1.0% (omitted by E); encoding 0.0% summarisation / 1.8% Q&A on GPT-3.5, "should only be used with appropriate LLMs". Authors recommend at least datamarking. Datamarking bypassed by payloads without spaces. Unvetted interaction: datamarking interleaves a marker between words and may break the "every number appears in a cited span" regex gate and DE/FR "1.234,56" formats.
- InjecGuard 2410.22770 [PREPRINT] (abstract only read): NotInject 339 benign samples; existing guards drop to about 60% accuracy (near random); "surpassing the existing best model by 30.8%" on the authors' own benchmark. Regulatory text contains "ignore", "instruction", "must": over-defense risk.
- DataSentinel 2504.11358 (IEEE S&P 2025, abstract): LLM detector, per-input LLM call (ingest only); ToolHijacker says detectors insufficient. No FPR figures.
- Anthropic prompt-injection research (2025-11-24): UNSUPPORTED numbers. "Sonnet 4.5 13.8% to 1.9%, Opus 4.5 8.0% to 1.4%" appear only in a chart, not in page text; quote "A 1% attack success rate ... still represents meaningful risk" CONFIRMED; internal 100-attempt Best-of-N attacker, browser-agent setting; classifiers not offered as an API product (NOT FOUND). Constitutional Classifiers "86% to 4.4%, +0.38% over-refusal, +23.7% compute": UNSUPPORTED (not rechecked); API availability NOT FOUND. Anthropic docs: untrusted content only in tool_result, JSON-encode, optionally screen with Haiku; no ASR stated.
- FinGround 2604.23588 [PREPRINT]: see 5.E5-numeric below.
- FinRegQA-EU 2609.36856 [ABS only]: LLM judges rewarded citation density; do not trust an LLM judge alone for citation quality.

### 4.3 Shortlist per guardrail point (from D, with caveats)

- User prompt: Presidio (in-process PII) + Model Armor PI/jailbreak in parallel with embedding; optional Prompt Guard 2 22M only if Model Armor latency or false positives fail (CPU latency must be benchmarked; Llama 4 licence and manual gating).
- Ingest chunks: Presidio for PII; Model Armor document screening per document (4 MB cap, quota-aware batching) for indirect injection; Prompt Guard 2 windows as fallback; spotlight/JSON-encode retrieved chunks at query time regardless.
- Model output: Presidio sentence-buffered redaction; deterministic citation verifier (ADR-009); Anthropic citations as an extra span signal only if structured output is not used; Model Armor response screen optional (adds latency).
- Not recommended: NeMo (latency), LLM detectors on hot path.

### 4.4 Model Armor free tier vs corpus size

- Free tier 2M tokens/month; 1M tokens of pricing = 4 chars excluding whitespace, so 2M tokens is about 8 MB of text per month (S1).
- Demo corpus about 10 MB text (A-us) exceeds the free tier on one full ingest screening; overage $0.10 per extra 1M tokens (cost trivial). Monthly tokens for ingest + queries + output checks not modelled (corpus tokens/month unknown).
- 1,200 QPM per project caps bulk chunk scanning: batch whole documents or throttle; files over 4 MB and inputs over 65,536 tokens (130,000 SDP) are skipped; handle EXECUTION_SKIPPED fail-closed explicitly.

---

## 5. Track E: RAG

Depth warning: E-rag-papers was read from arXiv abstracts only; skeptic re-read several. All papers are [PREPRINT] unless noted. Treat each as a hypothesis for ablation, not an effect size.

### E1 Tables and structured data
- Docling/TableFormer (2408.09869, 2501.17887): DocLayNet + TableFormer, MIT, commodity hardware; abstracts give no TEDS; published TEDS UNVERIFIED. Offline at ingest.
- VLM table-to-Markdown 2508.05669: fine-tuned Qwen2.5-VL-7B on Malaysian financial tables, 92.20% criteria accuracy, 96.53% Markdown TEDS on 100 tables; weak (100 tables, one region).
- PDF-to-RAG 2604.04948: 50 questions, 36 Portuguese docs; naive PDFLoader 86.2%, curated Markdown 91.3%, Docling + hierarchical splitting + image descriptions 94.1 +/- 1.6%; 33 pp swing from splitting on table questions; GraphRAG 82%; LLM-as-judge.
- HC-RAG 2608.12335: typed evidence graph, +6.6 F1 over RAPTOR on DocFinQA, +10.9 over GraphRAG on its own set; MimirRAG 2605.25030: 89.3% on FinanceBench (agentic, conflicts with latency budget); FinanceBench 2311.11944 baseline: GPT-4-Turbo with retrieval "incorrectly answered or refused 81%".
- Text-to-SQL over XBRL vs table chunking: no paper found. Deterministic lookup by (fund, class, tag) is an engineering inference (ablate as router arm).

### E2 Temporal / as-of retrieval
- FiscalQA Pro 2608.09393 (v1 2026-08-10) [PREPRINT]: 32,436 article-versions, French tax code 1938-2031; 209 questions over 33 articles; parametric 3.0%, static current-version RAG 2.7% [CI 1.3, 4.8], multi-version retriever C_prod 98.3% [95.9, 99.6], oracle-article 99.1% [98.4, 99.9]; gold version in top-5 for 99% vs 0% static; "a cross-encoder reranker adds nothing on this niche set"; residual gap is first-stage recall. CORRECTED interpretation: questions were selected as all-model-hard (current text lacks the gold value for 208 of 209), so 2.7% is a floor by construction; C_prod "conditions retrieval on the query date" and is the authors' own (weights not released); 98.3% needs an explicit as-of date in the query. Direction (hard validity filter beats current-only) solid; magnitude not transferable. Casual FinAdvisor questions may state no date; default date policy decides how often the filter acts.
- VersionRAG 2510.08109 [PREPRINT]: VersionQA 100 authored questions, 34 versioned technical docs; 90% vs naive 58% and GraphRAG 64%; 60% on implicit change detection (baselines 0-10%); 97% fewer indexing tokens than GraphRAG; software docs.
- No filter-vs-rerank head-to-head read; TimeQA/TempRALM not searched.

### E3 Multi-doc / multi-hop
- Adaptive-RAG 2403.14403 (NAACL 2024): classifier routes between no/single/iterative retrieval; numbers not read. IRCoT, Self-Ask ids from memory, not fetched; latency multipliers UNVERIFIED. Each hop is a sequential LLM call; >= 2 hops cannot meet TTFT p50 2.0 s (author estimate). Option inside budget: single-shot decomposition (one Haiku call, parallel retrieval, one generation); no paper compares it with IRCoT. RIT-RAG 2610.11370 agentic, +6.6 to 11.4 on EntQABench, outside budget.

### E4 Multilingual / cross-lingual
- LEMUR 2602.09570: 24,953 EUR-Lex PDFs, 25 languages; fine-tuning three multilingual embedders improves top-k, most for low-resource languages; supports HTML over PDF. No numbers in abstract.
- ChemCLIR-Bench 2609.23231: best Recall@10 falls 0.72 to 0.53 when query and document languages differ (not legal).
- Voyage MIRACL/MMTEB numbers NOT FOUND. Arm: EN query vs EN/DE/FR docs; baseline "translate query to doc language" (extra Haiku call).

### E5 Citations and verification
- ALCE 2305.14627 (EMNLP 2023): best models lack complete citation support 50% of the time on ELI5.
- Citation granularity 2604.01432 (v4, 2026-04-01) [PREPRINT]: sentence-level citations forfeit 2-97% (median 40%, up to 338% individual tasks) of attribution quality vs best granularity; correctness changes -2.3% to +4.4%; attribution peaks at paragraph level. Caveats: 8B-120B models, model-chosen citation units not UI highlighting, not legal/financial.
- VeriCite 2510.11394: multi-stage NLI check, no figures; async/post-hoc only.
- Numeric grounding, FinGround 2604.23588 [PREPRINT]: avg HalRate 4.1%, "78% relative reduction from GPT-4o + CoT (p<0.01)"; 68% reduction over strongest baseline at identical retrieval; 8B distilled detector 91.4% F1, 18x lower per-claim latency, $0.003/query; ablations 4.9 to 11.7 (FinanceBench, no taxonomy), 3.8 to 10.6 (TAT-QA, no table retrieval). Caveats: FinHalu is the authors' dataset (1,200 triples; kappa 0.83 in G, 0.87 in S2 check on 200), labels from GPT-4o, regeneration introduces errors in 4.1% of cases, detector transfers 3-4 F1 worse to other generators (Claude-3.5-Sonnet 87.6); HalRate is claim-level and LLM-judged, not an answer-level error rate. No paper found for a plain regex "number appears in cited span" gate; FiscalQA scores with regex/numeric tolerance (precedent). Own gate false-reject risks: rounding, derived numbers, units, DE/FR formats.
- Anthropic Citations API precision/recall: no figures (UNVERIFIED).

### E6 Chunking / contextual retrieval
- Anthropic contextual retrieval (https://www.anthropic.com/news/contextual-retrieval, 2024-09-19, CONFIRMED; E's "NOT CONFIRMED" resolved): top-20 retrieval failure 5.7% to 3.7% (35%) with Contextual Embeddings; to 2.9% (49%) with Contextual BM25; to 1.9% (67%) with reranking; Gemini Text 004, Cohere reranker, top-20; datasets codebases, fiction, ArXiv, science papers; $1.02 per million document tokens (2024 pricing + caching; recompute with Haiku 5.5 batch); "if your knowledge base is smaller than 200,000 tokens (about 500 pages) ... include the entire knowledge base in the prompt". CORRECTED use: baseline 5.7% is dense-only; 49% bundles contextual BM25 and 67% bundles a reranker, so only 35% is CR alone and none is "CR on top of hybrid+rerank". One embedding model, first-party blog, no legal/financial data.
- Mangla 2603.23533v4 (2026-03-08) [PREPRINT, single author, off-domain, 7B/120B open models, English; v1-v2 evaluation invalid per the author]: 7B enrichment beats free section-path prefix under hybrid by +5.5 recall on Qasper [3.3, 7.7]; FreshStack +2.7 [0.9, 4.7] not surviving Holm; enrichment equivalent to CR (H2 Qasper +2.1 [0.1, 4.0], FreshStack +1.8 [0.2, 3.4]) while CR sends 5.8-8.7x input tokens; under qwen3-embedding + reranker enrichment vs free prefix within equivalence margins; under BM25 +8.7; free prefix under either strong retriever beats hybrid enrichment by +3.4 to +6.3; best 120B-indexed config leads best free by +2.5 on Qasper; header-led chunks beat 512-char windows (+7.5) but lose to 256-token windows on FreshStack; late chunking lowers Qasper recall. Not "CR vs section prefix" directly: CR arm compared with enrichment. Gains concentrate under lexical retrieval; our FTS leg is not BM25.
- voyage-context-4 (https://docs.voyageai.com/docs/contextualized-chunk-embeddings, raw, CONFIRMED): chunks "encoded with the other chunks from the same document in view"; per chunk 32,000 tokens, 120,000 total, <= 1,000 inputs per request; $0.12/M; 3M TPM; no LLM call per chunk. CONTRADICTS E 6b "late chunking not available through Voyage API". No comparison numbers on the Voyage page.
- Reconstructing Context 2504.19754 [ABS]: CR preserves coherence at higher compute; late chunking efficient but loses relevance; no numbers. Late Chunking 2409.04701 numbers not read. Financial Report Chunking 2402.05131 [ABS]: element-type chunking "largely improve" results, no figures.
- LegalBench-RAG 2408.10343 [ABS]: 6,858 pairs, 79M chars; per-method results UNVERIFIED; contracts/privacy only.

### E7 Stats method on 150-300 items
- Template: Mangla pre-registered plan, Holm adjustment, equivalence margins (TOST-style) for "no difference".
- evalstats (see 1.6): judge calibration via PPI with a human-labelled set; rho^2 thresholds; CI advice at N<100.
- Sartori and Garcia 2605.27789 [ABS]: cluster-aware inference changed all-four-significant to one Bonferroni-significant: cluster by source document/regulation.
- "Noisy but Valid" 2601.20913 [ABS]: calibrate judge TPR/FPR on small human set. Eval-Pair Matrix 2607.10626 [ABS]: same-family judge self-leniency about 0 (-0.5 pp, CI [-2.7, +1.7]) on 275 records.
- Protocol (author synthesis, not sourced): paired design; binary metrics via McNemar exact test on discordant pairs; continuous via paired bootstrap over clusters; Holm across arms; 50-100 human labels for judge calibration with judge-human kappa; deterministic checks (cited ID exists, numbers in span). Power note (estimate, not computed): 200 items at ~10% discordance detects about a 7-8 pp swing. Tension: S2 flags evalstats advice against bootstrap CIs at N<100 vs clustered effective N.

### Candidate ablation arms
1. Context: free structural prefix (title + section path) vs voyage-context-4 vs LLM contextual retrieval (Haiku batch; 5.8-8.7x tokens; Anthropic $1.02/M 2024); flag default OFF until one wins. Predicted small gain for CR under strong retriever + rerank (Mangla, off-domain).
2. Temporal: hard validity-interval filter vs none (static current version); report separately the share of questions that state an as-of date.
3. Tables: markdown table chunk with caption/header repetition vs deterministic XBRL fact lookup router (RR numbers); Docling extractor with TEDS spot check on 20 KID cost tables.
4. Multi-doc: single-shot Haiku decomposition into parallel sub-queries vs plain retrieval, comparison questions only; no iterative loops.
5. Cross-lingual: EN query against DE/FR docs with voyage-4 directly vs query translation.
6. Citations: paragraph vs sentence granularity plus deterministic cited-ID and numeric-in-span checks (not LLM judge).
7. Injection: spotlighting/JSON-encoding default (check datamarking vs numeric gate and DE/FR formats); small classifier (InjecGuard-class) at ingest only, measure false positives on regulatory text.
8. Reranker: pin and ablate rerank-3 / rerank-3-lite (current in Voyage table) vs rerank-2.5 / rerank-2.5-lite (now "older"); same price ($0.05 / $0.02 per M); cost is not the issue.
- Stats: paired items across arms, cluster by document, Holm, equivalence margins for null claims, report n and SE per slice.

---

## 6. Open gaps

Track A
- eCFR official docs, rate limit, explicit terms (bot-check redirect); eCFR "unofficial" status.
- IAPD 2025+ file list, per-firm URL pattern, terms; brochure counts/sizes are estimates; ADV mapping-file columns uninspected; Data.gov monthly vs quarterly cadence.
- FINRA rule size and any permission programme; whether any FINRA bulk/API exists.
- FCA: written consent / Handbook licence agreement outcome; OGL cl.25 vs cl.13.3 revocation conflict; API format and rate number; COBS size; FCA API launch date (WEAK); FCA Register API data terms.
- CELLAR rate limits, Data Dump size, RSS registration; ESMA guidelines, FIRDS cadence, RSS URL, Q&A tool export; KID manufacturer terms (DWS, iShares, DB); KID table extraction untested; reason/date of UK PRIIPs revocation; second end-of-validity value on 2017/653; effective date of Del. Reg 2021/2268 (1 Jul 2022 vs 1 Jan 2023).
- Legal status of fund-company, adviser, KID reuse; SEC-hosted FINRA text.
- Eval: ai4privacy license.md (200k/300k/400k); SEC-QA data licence; FinanceRAG Kaggle terms; ObliQA-XRef terms; COLIEE; EUR-Lex-based QA beyond RegIR; deepset languages; PromptShield card; Lakera summarization size; HarmBench size; other 2025-2026 injection sets; toxic/off-topic sets; FinanceBench second-annotator process; labelling hours unsourced; golden-set items assumed independent.
- No real throughput measured on any ingest path (all limits are documented ceilings).

Track B
- Cloud SQL PITR retention days; standard backup/replica behaviour after key destruction; per-row purge from backups (docs silent).
- BigQuery AEAD crypto-shredding undocumented; DELETE bytes formula; DML on last-30-minute stream window not confirmed.
- GCS CMEK key-destruction effect; lifecycle conditions and latency; Cloud Logging bucket-level CMEK on key destruction and per-GiB pricing.
- Confluent Basic: retention.ms numeric max and infinite retention on Basic; actual erasure latency; Cloud Basic raw pricing page not read.
- KMS per-operation token cost against the 100 write TPM quota.
- Langfuse: dataset items after trace delete; no deletion rate number.
- Dagster: blocking checks across runs/schedules/partitions, concurrency limits during backfill, Declarative Automation vs auto-materialize.
- pgvector: CHANGELOG, behaviour under RLS and LIST partitions; Cloud SQL 0.8.5 vs README 0.8.7.
- Not covered: Great Expectations fit, dbt-to-OpenLineage, Fivetran; no primary write-up for LinkedIn, Uber deletes, Segment; no "proof of deletion" design; Iceberg claims secondary; Anthropic Batch 50%/24 h/29-day facts UNCHECKED.
- Hash-based change-detection and temporal-vector-index production write-ups thin (Exa rate-limited).

Track C
- Same email in several Identity Platform tenants; session cookies per tenant; Identity Platform data location; OIDC per-tenant setup; cross-region token verification statement.
- All GCP unit prices (Cloud SQL, Cloud Run, BigQuery, GCS, ALB, Armor) and Langfuse second-account price; Cloud SQL stop-when-idle behaviour; Cloud SQL cross-region replica on Enterprise (non-Plus) edition; Cloud Run multi-region GA/preview status; Cloud Armor cross-region attachment; ALB header routing; GCS London-Frankfurt dual-region.
- Voyage regions/Marketplace; Claude on Vertex EU endpoints and regions.
- No published multi-region-membership login pattern; no Salesforce org-migration, Stripe or Notion residency detail.

Track D
- Model Armor latency, SLA, per-feature GA status, precision/recall, ingest-volume pricing model; Presidio latency and recall; NeMo overhead; Prompt Guard 2 CPU latency and Llama 4 licence text; Constitutional Classifiers API availability; Claude figures for Spotlighting; Presidio/NeMo/Qwen3Guard numbers not rechecked by skeptic; Anthropic prompt-injection chart values; PromptGuard, Instruction Hierarchy, BIPIA, AgentDojo ASR/FPR; DataSentinel/PIGuard FPR.

Track E
- Full-text reads of 2608.09393 (per-model table), 2603.23533, 2604.23588, 2609.35815 results sections (A: two re-read by skeptic from abstract/in-text only); Docling TEDS; TAT-QA; text-to-SQL vs table chunking; Voyage MIRACL/MMTEB and voyage-context-4 comparison numbers; IRCoT/Self-Ask/Adaptive-RAG latency; ALCE/AlignScore accuracy and Anthropic Citations figures; TimeQA/TempRALM and filter-vs-rerank; InjecGuard full text (published venue unchecked).
