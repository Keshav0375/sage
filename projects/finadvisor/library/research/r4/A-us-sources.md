# EVIDENCE — R4 Track A (US sources). Read 2026-11-02 (today per session). Author: docs-reader (Sonnet).
Method: WebFetch of official pages + live curl probes of official endpoints (probes are labelled PROBE and are measured facts, not doc quotes). All SEC probes used a declared User-Agent, <=2 req/s. Quotes come from WebFetch extractions (small-model extraction; load-bearing quotes should be spot-checked before an ADR). Items I could not verify are marked UNVERIFIED.

## 0. Summary table

| Source | Licence / terms | Access | Size | Update / change detection | Verdict |
|---|---|---|---|---|---|
| eCFR (17 CFR 275 etc.) | US gov work; explicit terms page UNVERIFIED | REST, no key, needs gzip | Pt 275 = 223k chars; Pt 270 = 784k; Title 17 = 17.3M | `titles.json` up_to_date_as_of; `versions/` per section with amendment_date/issue_date/removed | Use. Best source, point-in-time native |
| FINRA Rulebook | Terms FORBID copying, bulk, scraping, DB build, ML | none (no API/bulk found) | n/a | Updates page + Reg Notices, no feed found | DO NOT ingest without written permission |
| EDGAR 497K/N-1A/N-PORT | "public information... may be copied" | Archives, data.sec.gov JSON, quarterly datasets | see sec. 3 | daily-index, full-index, submissions JSON | Use (10 rps + UA) |
| EDGAR XBRL companyfacts/frames | same | data.sec.gov | zip 1.41 GB | nightly ~3am ET | NOT usable for fund RR data (PROBE: 404 for fund trust) -> use RR datasets |
| IAPD Form ADV 2A | No separate terms on SEC page; IAPD terms UNVERIFIED | SEC zip archives (monthly) + per-firm PDF | 400-660 MB zip/month (2024) | monthly zips, mapping CSV | Use SEC archive for bulk; demo = per-firm PDFs |

## 1. eCFR API (www.ecfr.gov/api/...)

### Confirms
- Official developer docs page could not be read: it 302-redirects to unblock.federalregister.gov (bot-check) for both WebFetch and curl. I did NOT work around it. PROBE: `https://www.ecfr.gov/developers/documentation/api/v1` -> `HTTP/2 302 location: https://unblock.federalregister.gov` (2026-11-02). Doc-stated rate limits, terms, and endpoint list therefore UNVERIFIED from the vendor page. A web-search snippet (not official) gave base `https://www.ecfr.gov/api/versioner/v1`, docs at `/developers/documentation/api/v1`, search at `/api/search/v1`, admin at `/api/admin/v1`, no API key.
- Endpoints verified by PROBE (HTTP 200, 2026-11-02):
  - `GET /api/versioner/v1/titles.json` -> per title `latest_amended_on`, `latest_issue_date`, `up_to_date_as_of`. Title 17: `"latest_amended_on":"2026-10-19","latest_issue_date":"2026-10-29","up_to_date_as_of":"2026-10-29"`.
  - `GET /api/versioner/v1/versions/title-17.json?part=275` -> `content_versions[]` with `date, amendment_date, issue_date, identifier, name, part, substantive, removed, subpart, type`. 143 records, 48 distinct section ids, amendment_date range 2016-12-31..2025-03-12, max issue_date 2026-10-28, 9 records `removed:true` (e.g. 275.206(4)-3, 275.206(4)-4, 275.206(4)-9, 275.206(4)-10, 275.211(h)(1)-1). So 275 history covers only 2016-12-31 onward (data starts at 2017 CFR-edition era; UNVERIFIED as a documented limit).
  - `GET /api/versioner/v1/full/{date}/title-17.xml?part=275` -> 200, 225,395 bytes XML (DIV5 PART, 39 DIV8 sections at 2026-10-29). Date 2020-01-01 also works (46,923 B gz-transferred / point-in-time works). Section-level: `...&section=275.206(4)-1` -> 6,568 B.
  - `GET /api/versioner/v1/structure/{date}/title-17.json` -> JSON tree with `size` per node. Part sizes (chars): 275=222,985; 270=784,294; 274=35,346; 279=6,032; 230=1,041,030; 240=3,792,563; 242=678,216; 249=95,679; 210=568,342; Title 17 total 17,320,268; Chapter II 10,997,000.
  - `GET /api/versioner/v1/ancestry/{date}/title-17.json?part=275&section=...` -> 200.
  - `GET /api/search/v1/count?query=adviser` -> `{"meta":{"total_count":1758,...}}`; `GET /api/search/v1/results?query=...&hierarchy[title]=17&per_page=1` returns hits with `starts_on`, `ends_on` (so search spans historic versions) and `full_text_excerpt`.
- Compression required — PROBE: without Accept-Encoding the full endpoint returns `This endpoint requires response compression. Send an Accept-Encoding header that permits compression.` (HTTP 406). Use `Accept-Encoding: gzip`.
- Format: XML (full), JSON (structure/versions/search). HTML/PDF render exist on site (UNVERIFIED for API).
- Language: English. Jurisdiction: US federal.
- Licence: eCFR is a US Government publication; explicit eCFR terms/public-domain statement UNVERIFIED (docs page blocked). The eCFR is "unofficial" editorial compilation per its site (UNVERIFIED, not read). The SEC rule *text* is public information.
- Update frequency: Title 17 `up_to_date_as_of` 2026-10-29 vs today 2026-11-02 (lag a few days, PROBE). Daily-ish (UNVERIFIED as doc statement).
- Change/delete detection: (a) poll `titles.json` and compare `up_to_date_as_of`/`latest_issue_date` for title 17; (b) poll `versions/title-17.json?part=N` and diff on (identifier, amendment_date, issue_date); `removed:true` = deletion/withdrawal; `substantive:false` = non-substantive (editorial, e.g. heading rename) issue. Query filters `issue_date[gte]` etc. documented only in third-party material; I did not verify they filter (UNVERIFIED).
- Rate limit: not found in readable official source -> UNVERIFIED. Be conservative (<=1-2 rps, cache by date; point-in-time XML is immutable per date).
- Bulk alternative: govinfo bulk (`https://www.govinfo.gov/bulkdata/ECFR/title-17/ECFR-title17.xml`) returned HTTP 200 and 4.69 MB on PROBE; I did not validate content/completeness -> UNVERIFIED.

### Improvements
- Use `versions/` + `full/{date}` per section (section as chunk unit = DIV8). Store `amendment_date` as effective-from, next version date as effective-to; treat `removed:true` as tombstone.

## 2. FINRA Rulebook

### Contradicts (blocker)
- Terms of Use (Last modified: November 9, 2023; read 2026-11-02) https://www.finra.org/terms-of-use :
  - "the content and material provided through the FINRA Website shall be used ONLY for your own" (non-commercial personal/professional use)
  - "may not be copied, reproduced, transmitted, displayed, performed, distributed, rented, sublicensed" ... "without FINRA's prior written consent"
  - Prohibited: "use any process to monitor or copy the FINRA Website in bulk"; "use any data mining, scraping or harvesting tools (including robots)"; "develop or create a database of data using the FINRA Website"; "use any portion of the FINRA Website in the development of any software program"; "in conjunction with any machine learning, neural network, deep learning, predictive analytics" (extraction truncated; full sentence not captured -> read the page before relying on exact scope).
  - Request path: "To request permission to use any FINRA-copyrighted material" contact FINRA. Copyright "© 2026 FINRA. All Rights Reserved."
  => A multi-tenant RAG product copying/embedding the FINRA Rulebook is prohibited without written permission. Even a demo that scrapes it is prohibited.
- API/bulk: https://www.finra.org/rules-guidance/rulebooks (read 2026-11-02) says nothing about API, download or copying. No official bulk/API found -> UNVERIFIED that none exists.
- Change notices: Rulebooks page lists "Immediately Effective Rule Changes Pending Issuance of a Regulatory Notice", "Immediately Effective Rule Changes Pending SEC Notification", "Approved Rule Changes Pending Determination of Effective Date", and "Updates" (/rules-guidance/rulebooks/updates). Updates page lists rules with dates (e.g. "Rule 4210, Margin Requirements (Oct 22, 2026)", "Rule 3290 (Oct 25, 2027)" - effective dates) with date filter 30/15/5 days; no RSS/feed mentioned. Reg Notice numbers not listed there.
- Size: rule count/bytes UNVERIFIED (not measured; scraping prohibited).
- Alternatives (INFERENCE, not verified legally): SEC-hosted rule-filing documents (sec.gov/rules/sro) are SEC web content ("may be copied or further distributed" per SEC page), but I did not verify FINRA-authored text status there. Ask FINRA for a licence or exclude. Flag to legal.

## 3. SEC EDGAR

### Terms / fair access (all read 2026-11-02)
- https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data (Last Reviewed or Updated: June 26, 2024): "Current max request rate: 10 requests/second." ; "declare your user agent in request headers" (sample "Sample Company Name AdminContact@<sample company domain>.com"); "Download only what you need and please moderate requests to minimize server load."; "Anyone can access and download this information for free."; "We do not offer technical support for developing or debugging scripted processes."
- https://www.sec.gov/about/privacy-information (Last Reviewed or Updated: Nov. 29, 2023): "Information presented on sec.gov is considered public information and may be copied or further distributed" ; "Please consider appropriate citation to the SEC as the source."; "The SEC does not allow "unclassified" bots or automated tools to crawl the site."; "We reserve the right to block IP addresses that submit excessive requests." Access resumes once rate stays below the limit for 10 minutes. Do not use SEC seal/logos.
- Licence summary: free to copy/redistribute; no SEC permission needed; cite SEC; no logos. Third-party content inside filings (e.g. fund-company copyrighted text) is not addressed by the SEC page -> UNVERIFIED legal question.

### Index / change detection
- Same access page: indexes "from 1994Q3 through the present"; "daily index files through the current year" in /Archives/edgar/daily-index; /Archives/edgar/full-index covers quarters; four index types: company, form, master, XBRL; each directory has index.html/.xml/.json. "Feed directory (/Archives/edgar/Feed/)": tar+gzip per filing day (page does not describe in "bulk" terms). Also: "Corrections and removals may change filings after acceptance, and full and quarterly indexes are rebuilt weekly on Saturday mornings to reflect them." -> removals/deletes are only reflected in the weekly rebuild; daily index is append-oriented.
- PROBE: `/Archives/edgar/daily-index/2026/QTR4/index.json` lists `company.20261001.idx` (792 KB) ... per day with `last-modified`. `full-index/2026/QTR3/form.idx` = 47.2 MB, "Last Data Received: September 30, 2026"; counts of rows for Q3 2026: 497K 4,581; 485BPOS 833; NPORT-P 13,950; N-1A 19 (grep on line prefix; approximate).
- Submissions JSON PROBE (Vanguard Index Funds CIK 36405): `filings.recent` has 1000 rows with accessionNumber, filingDate, reportDate, acceptanceDateTime, form, size, isXBRL, isInlineXBRL, primaryDocument; older rows in `filings.files[]` (e.g. `CIK0000036405-submissions-001.json`, 1,460 filings 1994-02-02..2018-06-21). Per-CIK submissions poll = per-fund-family change detection (new accession, `acceptanceDateTime`). Amendments are separate form types (/A). Deletions: no per-filing tombstone seen (UNVERIFIED).

### 497K / N-1A (summary prospectus, statutory prospectus)
- PROBE (Vanguard Index Funds, recent 1000 rows): 363 are 497K, 65 are 497; 497K median primary doc 106,276 bytes (HTML, `isXBRL=0`), e.g. 130-137 KB each; 485BPOS (post-effective amendment carrying the N-1A prospectus) 75,069,932 bytes with inline XBRL (isInlineXBRL=1). 497K range in that sample 2019-04-26..2026-04-28.
- Formats: HTML (primary), SGML submission text; PDF not typical (UNVERIFIED). Language English. Jurisdiction US.
- History: every filing is immutable; "point-in-time" = filing date. Annual refresh cadence by fund (April-ish for Vanguard sample).

### XBRL RR (risk/return)
- companyfacts/frames: https://www.sec.gov/search-filings/edgar-application-programming-interfaces (Last Reviewed or Updated: April 8, 2025): "Each entity's current filing history is available at" data.sec.gov/submissions/CIK##########.json ; companyfacts "returns all the company concepts data for a company into a single API call"; Frames "aggregates one fact for each reporting entity that is last filed"; "submissions.zip ... contains the public EDGAR filing history for all filers"; "companyfacts.zip ... contains all the data from the XBRL Frame API and the XBRL Company Facts API"; APIs "updated in real time" and bulk ZIPs "republished nightly at about 3:00 a.m. ET" (paraphrase by extractor; page text not exact); "data.sec.gov does not support Cross Origin Resource Scripting (CORS)." Page mentions no rate limit (10 rps general rule applies).
- Bulk PROBE (HEAD, 2026-11-02): `/Archives/edgar/daily-index/xbrl/companyfacts.zip` 1,414,913,699 B, last-modified Sat 31 Oct 2026 04:23 GMT; `/Archives/edgar/daily-index/bulkdata/submissions.zip` 1,572,128,284 B, last-modified 2026-10-31 04:31 GMT.
- CONTRADICTS the design assumption: PROBE `data.sec.gov/api/xbrl/companyfacts/CIK0000036405.json` (Vanguard Index Funds) -> 404 NoSuchKey. Frames for taxonomies `rr`, `dei`, `invest` -> 404 (us-gaap frame returns 200, 184,617 B). So mutual-fund RR facts are NOT available through companyfacts/frames (at least for this registrant). Use the RR datasets instead:
- Mutual Fund Prospectus Risk/Return Summary Data Sets (https://www.sec.gov/data-research/sec-markets-data/mutual-fund-prospectus-riskreturn-summary-data-sets, Last Reviewed or Updated: June 30, 2026): "text and numeric information extracted from the risk/return summary section of mutual fund prospectuses"; "The data sets will be updated quarterly."; quarterly ZIP; range "December 2010 - June 2026"; ZIP sizes "about 97 KB (2010 Q4) to about 78 MB (2026 Q2)"; disclaimer "we cannot guarantee the accuracy of the data sets" and "are not a substitute for such filings". PROBE: `.../files/dera/data/mutual-fund-prospectus-risk/return-summary-data-sets/2026q2_rr1.zip` 81,661,882 B, last-modified 2026-07-14. Filers after 5:30 PM ET on last business day go to next quarter. Q3 2026 not yet posted as of the page (lag ~2 weeks+).
- N-PORT data sets (https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets, Last Reviewed or Updated: Sept. 30, 2026): "contain information derived exclusively from structured data filed with the Commission"; "updated quarterly"; quarterly ZIP "about 228.89 MB (2019 Q4) to 690.83 MB (2022 Q3)", most 317-483 MB; range "October 2019 - September 2026". PROBE 2026q3_nport.zip 462,371,568 B (note: URL path guessed from RR pattern; resolved 200).
- EDGAR FTS: https://www.sec.gov/edgar//search/efts-faq.html (read 2026-11-02): "search the full text of all EDGAR filings submitted electronically since 2001"; includes "all attachments (such as exhibits)". No official API documentation found; the FAQ does not mention an API, indexing latency, or a result cap. PROBE of efts endpoint returned HTTP 403; I did not attempt to bypass. Third-party claims (10k result cap, 10 rps) UNVERIFIED. Recommend NOT building on FTS; use submissions + daily-index.

### Cost
- All free. Egress/storage only on our side.

## 4. IAPD Form ADV Part 2A brochures

- https://www.sec.gov/foia-services/frequently-requested-documents/form-adv-data (Last Reviewed or Updated: Dec. 16, 2025; read 2026-11-02): "Form ADV Data from January 1, 2025, to present is available on the Investment Adviser Public Disclosure website" (adviserinfo.sec.gov/adv; the page is JS-rendered and WebFetch returned only a title, so file list there is UNVERIFIED). "Form ADV Part 2 brochures and Form ADV Part 3 CRS are available below in .pdf format." "The SEC does not have access to data for state-registered investment advisers." (FINRA holds state data.) Historical Part 1/ADV-W: CSV. The page has no separate terms of use and states no update schedule; files are posted by month.
- Sizes listed (2024 Part 2 brochure zips, monthly): Jan 610 MB, Feb 539 MB (+ Part 1 481 MB), Mar 10 parts 511-629 MB each, Apr 611, May 663, Jun 534, Jul 452, Aug 489, Sep 511, Oct 531, Nov 385, Dec 405 MB -> roughly 11-12 GB zipped per year of Part 2. Part 3 CRS monthly zips 58-136 MB. Mapping file (March 2024) 2.06 MB. 2020-2023 sizes not listed.
- Archive (https://www.sec.gov/foia/form-adv-part-2-data-archive, Last Reviewed or Updated: Jan. 6, 2026): years 2007-2019, "Every linked file is a ZIP archive"; split in numbered parts (2012: 8, 2015: 10, 2017: 10, 2018/2019: 11); no sizes shown.
- Data.gov listing (via search snippet, not opened): Part 2 PDFs "from April 2007 through the most recent quarter"; "allow approximately one month after the quarter ends" - cadence conflicts (monthly vs quarterly) -> UNVERIFIED; trust SEC page (monthly files).
- Brochure count: ~15-16k SEC-registered advisers (UNVERIFIED, no SEC page read; estimate). A single brochure PDF is typically 0.1-several MB (PROBE: IAPD per-firm doc `reports.adviserinfo.sec.gov/reports/ADV/105958/PDF/105958.pdf` returned 200, application/octet-stream, 8,119,546 B; this is the per-firm ADV report PDF, possibly Part 1+2, not necessarily the Part 2A brochure; undocumented URL pattern).
- Per-firm brochure access, rate limit, and IAPD terms of use: UNVERIFIED (adviserinfo.sec.gov pages not text-readable; no terms page read). Third-party APIs (sec-api.io) exist; not official.
- Language: English. Jurisdiction: US (SEC-registered only). Format: PDF (brochures), CSV (Part 1).
- Change detection: new monthly zip + "Mapping Information" CSV (maps firm/brochure ids); brochure versions: amendment dates inside mapping file (UNVERIFIED, mapping columns not inspected); withdrawals via Form ADV-W monthly CSV (2024 monthly sizes 7.5-38 KB) and the 2025+ IAPD site (UNVERIFIED).
- Note: SEC page says nothing about copyright of brochure content. Brochures are firm-authored public disclosures; reuse in a commercial product is a legal question -> UNVERIFIED.

## 5. Smallest useful US demo subset (design suggestion, sizes measured/estimated)

- Rules (eCFR, point-in-time): 17 CFR 275 whole part (39 sections now, 223k chars ~ 55-60k tokens, 225 KB XML) + versions history (143 version records) to demo "as of date" answers. Add 17 CFR 270 selected rules? Whole Pt 270 is 784k chars (~200k tokens): optional. Suggested: Pt 275 (full) + Pt 279 (6k chars) + a few of Pt 270 (e.g. 270.38a-1? not verified) -> ~1 MB XML total.
  Minimum "N rules": 275.206(4)-1 (marketing rule, 4 versions 2016/2021/2022, section XML 6.5 KB... note that is the 2026 version), 275.204-2 (books/records), 275.206(4)-7 (compliance), 275.204A-1 (code of ethics), 275.206(3)-2 (principal trades) = 5-10 rules, <150 KB.
- Funds (EDGAR): 3 fund families, e.g. Vanguard Index Funds (CIK 36405), plus two more of your choice; ~10-15 497K summary prospectuses each (HTML ~100-140 KB each, 1.5 MB per family, ~5 MB total). Avoid 485BPOS (up to 75 MB each). RR dataset quarter 2026q2_rr1.zip (82 MB) optional for structured cross-checks; N-PORT quarter (462 MB) not needed for demo.
- Adviser brochures: 10-20 firm Part 2A PDFs fetched individually (assume ~1-8 MB each, 20-100 MB); the SEC monthly zip (400-660 MB) only if bulk needed. Legal check before shipping.
- FINRA: none (terms prohibit).
- Total demo corpus: ~10 MB text + <=100 MB PDFs. Production-bulk upper bound: companyfacts 1.4 GB + submissions 1.6 GB (not needed for RAG).

## Vendor recommends
- SEC: "Download only what you need and please moderate requests"; declare User-Agent; <=10 rps; no unclassified bots. Use `Accept-Encoding: gzip, deflate` and Host (access page).
- eCFR: send compression header (server error message). No other vendor guidance readable.

## Changes / watch
- SEC Form ADV data moved to IAPD site from 2025-01-01 (SEC FOIA page).
- N-PORT and RR quarterly datasets are current to Sept 2026 / June 2026 respectively.

## Improvements (what docs suggest we change)
1. Drop FINRA Rulebook from the corpus (or get written licence); substitute SEC-hosted rule text; note design must not scrape finra.org.
2. Do not plan on companyfacts/frames for fund RR facts; use RR quarterly datasets or parse 497K/485BPOS inline XBRL.
3. eCFR: use `versions/` as the change feed; section-level chunks keyed (identifier, amendment_date); handle `removed:true` and issue_date-only (non-substantive) changes.
4. EDGAR change detection: per-CIK submissions JSON + daily-index; run a weekly reconcile against the full-index (Saturday rebuild) to catch removals.
5. Set a single egress rate limiter (<=5 rps) and one declared UA per tenant-agnostic ingestion service.

## Gaps
- eCFR official developer docs, rate limits and explicit terms: UNVERIFIED (bot-check redirect).
- IAPD 2025+ data file list, per-firm brochure URL pattern and terms: UNVERIFIED (JS site).
- FINRA rulebook size and any permission programme: UNVERIFIED.
- Legal status of fund-company and adviser-authored text reuse: UNVERIFIED.
- Total brochure count and per-brochure PDF size: estimate only.
- Quotes are from WebFetch extractions (small model); spot-check before an ADR.
