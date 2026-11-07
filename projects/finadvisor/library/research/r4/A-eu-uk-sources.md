# EVIDENCE - R4 Track A: EU + UK public source catalogue

Read 2026-11-01 and 2026-11-02. Method: official pages fetched through Exa reader (WebFetch returned empty for EUR-Lex), plus live probes with curl against CELLAR and legislation.gov.uk (marked PROBE). Page-reader leaves were not used. All quotes are copied from the fetched text. UNVERIFIED = not confirmed from an official page.

## 1. EUR-Lex / CELLAR

### Confirms
- Licence: reuse for commercial and non-commercial purposes, based on Decision 2011/833/EU. - "The Commission's document reuse policy is based on Decision 2011/833/EU. Unless otherwise specified, you can re-use the legal documents published in EUR-Lex for commercial or non-commercial purposes." - https://eur-lex.europa.eu/content/legal-notice/legal-notice.html (read 2026-11-01)
- Consolidated texts are CC BY 4.0 (attribution + indicate changes). - "the summaries of EU legislation and the consolidated texts, which is owned by the EU, is licensed under the Creative Commons Attribution 4.0 International licence ... you can re-use the content provided you acknowledge the source and indicate any changes you have made." - same URL (read 2026-11-01)
- Only the Official Journal is authentic. - "Only European Union documents published in the Official Journal of the European Union are deemed authentic." - same URL. Consequence: consolidated versions are not legally authentic; the corpus must label them as such.
- Some documents carry special terms. - "Some documents, like the International Accounting Standards, may be subject to special conditions of use" - same URL.
- Access paths: SOAP web service (registration), CELLAR SPARQL + REST, Data Dump, RSS notifications. - "Cellar data can be accessed directly through the SPARQL endpoint and the RESTful API ... Both options are available in several formats (PDF, HTML, Formex, etc.)" (Spanish original, translated) - https://eur-lex.europa.eu/content/help/data-reuse/reuse-contents-eurlex-details.html (read 2026-11-01)
- SOAP web service: free, registration, search only, no file download. - "This web service is based on the SOAP protocol and is freely available after registration. ... it cannot be used to directly download the document files." - https://eur-lex.europa.eu/content/help/data-reuse/webservice.html (read 2026-11-01). Registration form asks for "Maximum number of calls per day"; limits are per-user and changeable on request.
- CELLAR REST needs no registration. - Table row "Registration | Required ... | Not required - open and publicly accessible." - https://eur-lex.europa.eu/content/tools/webservices/DataExtractionUsingWebServices.pdf (v3.0.0, read 2026-11-01)
- SPARQL endpoint URL: https://publications.europa.eu/webapi/rdf/sparql - "The Knowledge Graph interface is available at : https://publications.europa.eu/webapi/rdf/sparql" - https://op.europa.eu/documents/d/cellar/cellar_ml_dataset_guide (read 2026-11-01). PROBE 2026-11-01: anonymous GET with Accept text/csv and application/sparql-results+json returned HTTP 200.
- Content negotiation, Formex and XHTML. - `curl -H "Accept:application/zip;mtype=fmx4" -H "Accept-Language:eng" -L http://publications.europa.eu/resource/celex/32024D1738` - DataExtractionUsingWebServices.pdf. PROBE 2026-11-01: this worked for 32014R1286 (200, 27,662 B zip with Formex XML, EN).
- Languages: 23-24 per act. PROBE (SPARQL count of expressions per language): 32014L0065 = 23, consolidated 02014L0065-20250117 = 23, 32014R1286 = 24.
- Consolidated versions are separate CELEX numbers 0YYYYXNNNN-YYYYMMDD. PROBE (SPARQL on cdm:resource_legal_id_celex), 2026-11-01:
  - MiFID II 02014L0065: 14 versions, 20140917 ... 20260606.
  - MiFIR 02014R0600: 11 versions, 20140702 ... 20251123.
  - PRIIPs 02014R1286: 5 versions, 20141229 ... 20240109.
  - Delegated Reg 2017/565 (02017R0565): 6 versions, 20170331 ... 20220802.
  - RTS 2017/653 (02017R0653): 6 versions, 20170412 ... 20230101.
  - Total 42 consolidated versions for the 5 acts (EN set; each exists in about 23 languages).
- Consolidated text is retrievable as XHTML in several languages. PROBE: `Accept: application/xhtml+xml` + Accept-Language eng/deu/fra on http://publications.europa.eu/resource/celex/02014L0065-20250117 returned 200 with 956,709 / 1,005,431 / 1,044,217 bytes. Formex zip for the consolidated version also returned 200 (109,982 B zip). `text/html` and `application/pdf;type=pdfa1a` returned 404 for the consolidated CELEX (PDF/HTML must be fetched via the EUR-Lex URL form, UNVERIFIED).
- ELI identifiers exist in CELLAR. PROBE: cdm:resource_legal_eli = http://data.europa.eu/eli/dir/2014/65/oj ; http://data.europa.eu/eli/reg_del/2017/653/oj.

### Limits
- SOAP search cap. - "From 1 January 2026, the number of results returned by a single search will be limited to 10 000." - webservice.html (read 2026-11-01)
- Mass volume must not use SOAP. - "For large volumes of data use one of the mass data download services like Direct access to the CELLAR API or Data Dump." - webservice.html
- Data Dump covers legal acts in force by language and needs an EU Login account. - "currently you can bulk download all legal acts (CELEX sector 3) in force by language ... you will need an EU Login account" (Spanish original, translated) - reuse-contents-eurlex-details.html. Size of the dump: UNVERIFIED (not stated).
- CELLAR REST/SPARQL rate limits: no published figure found. UNVERIFIED. Treat as undocumented; throttle client-side.
- Size basis (PROBE): consolidated MiFID II XHTML ~1 MB per language; PRIIPs Regulation Formex 115 KB XML (original). Five acts x 42 versions would be ~40 MB XHTML in one language (estimate, not an official figure).

### Change, corrigendum and repeal detection
- RSS per change. - "Notifications through the database's RSS, which will tell you of every specific change. The RSS can produce a very large number of notifications (millions per day)." (Spanish, translated) - reuse-contents-eurlex-details.html. Also - "The CELLAR provides also an RSS feed in order to allow reusers to receive information about new documents that have been loaded into the repository or updates of existing data." - https://data.europa.eu/data/datasets/sparql-cellar-of-the-publications-office (read 2026-11-01). Whether RSS needs a request or registration: the page says "can request", UNVERIFIED.
- Poll alternative (PROBE): cdm/cmr#lastModificationDate on the work (MiFID II 32014L0065 = 2026-04-30T14:18:21+02:00; RTS 32017R0653 = 2023-09-19). SPARQL on this property gives a polling delta without RSS.
- In-force and end-of-validity are in the graph. PROBE: cdm#resource_legal_in-force = 1, resource_legal_date_end-of-validity = 9999-12-31 for MiFID II. For 32017R0653 two end-of-validity values appear (2022-12-31 and 9999-12-31); meaning of the first is UNVERIFIED.
- Repeals: cdm:resource_legal_repeals_resource_legal / resource_legal_does_repeal_of_resource_legal (PROBE, MiFID II repeals 5 works).
- Corrigenda are separate CELEX numbers 3YYYYXNNNNR(nn). PROBE: MiFID II R(01)-R(19); MiFIR R(01)-R(11); PRIIPs R(01)-R(08); 2017/565 R(01)-R(09); 2017/653 R(01)-R(08). The first-listed corrigenda numbers include corrigenda to translations, so they are language-specific (inference from numbering, UNVERIFIED).
- New consolidated version appears as a new CELEX with a new date suffix; the previous one stays (PROBE above).

### Contradicts / caveats
- WebFetch of eur-lex.europa.eu returned empty pages and plain curl got HTTP 202 empty (anti-bot). Use the Exa reader or the CELLAR endpoints, not page scraping.
- Consolidated texts are free under CC BY 4.0 but "not authentic"; amending the corpus with a "consolidated, no legal value" flag is advised.

### Other items asked
- Delegated Reg 2017/565, MiFIR, PRIIPs Reg and RTS 2017/653: same access path, CELEX 32017R0565, 32014R0600, 32014R1286, 32017R0653. RTS 2017/653 was amended by Delegated Reg 2021/2268 (applicable from 1 January 2023 for the KID presentation; the Delegated Reg itself says "It shall apply from 1 July 2022", later moved) - https://eur-lex.europa.eu/eli/reg_del/2021/2268/oj/eng ("In force: This act has been changed. Current consolidated version: 14/07/2022"). The 2021/2268 page and the JC Q&A disagree on date wording (1 July 2022 in the act text vs 1 January 2023 in the Q&A, which reflects a later extension). Mark date UNVERIFIED until the extension act is read.
- Formats: PDF, HTML, XHTML, Formex 4 (Official Journal acts), RDF/XML notices.

## 2. ESMA

### Confirms
- Terms: reproduction authorised with source acknowledgement. - "Reproduction of all information on this site (ESMA Library) is authorised except as otherwise stated, provided the source is acknowledged and: ..." - https://www.esma.europa.eu/about-esma/legal-notice-and-data-protection (read 2026-11-01). Conditions: when sold, say it is free from ESMA; when transformed (summary, translation) state "This document has been drafted using material downloaded from ESMA's website" plus the non-endorsement text; no implied endorsement.
- Legislative text is excluded from ESMA's copyright. - "This copyright does not extend to any legislative text which is publicly available or to other third party's materials." - same URL.
- Registers have the same notice. - https://registers.esma.europa.eu/publication/legalNoticePage (read 2026-11-01).
- Q&As on MiFID II/MiFIR investor protection: PDF frozen. - "Please note that this document is not updated after 31 December 2023. For Q&As issued from 1 January 2024, please search in the ESMA Q&A IT-tool." (ESMA35-43-349, dated 15 December 2023) - https://www.esma.europa.eu/sites/default/files/library/esma35-43-349_mifid_ii_qas_on_investor_protection_topics.pdf (read 2026-11-01). Sections carry "[Last update: date]", e.g. "9 Information on costs and charges [Last update: 15 December 2023]". About 18 sections.
- The Q&A tool lists new items with IDs and dates (e.g. ESMA_QA_2952, 20/10/2026) at https://www.esma.europa.eu/esma-qa-search-page ; rejected questions also appear at .../esma-qa-search-page/rejected (read 2026-11-01). Export of the tool as bulk/API: UNVERIFIED. A print view as PDF exists: https://www.esma.europa.eu/print/view/pdf/esma_q_a_search_page/page_2 .
- PRIIPs Q&A is a Joint Committee document hosted on ESMA/EBA/EIOPA sites. Latest found: JC 2023 22 dated 5 December 2025 - https://www.esma.europa.eu/sites/default/files/2023-05/JC_2023_22_-_Consolidated_JC_PRIIPs_Q_As.pdf . Earlier snapshots: 28 June 2024, 15 March 2024 (EBA URLs), JC 2017 49 of 21 December 2022. Same file name, new content: URL stable, version in the text date.
- Deletions are documented. JC PRIIPs: "these Q&As needed to be revised or deleted. These revisions or deletions were published on 21 December 2022 and in these cases it is specifically indicated underneath the answer." ESMA Prospectus Q&A: "Overview of changes made to the Prospectus Q&As" lists items with "Deleted" = X and reasons (e.g. "The answer is clear based on the law.") - https://www.esma.europa.eu/sites/default/files/2026-09/Overview_of_changes_made_to_the_Prospectus_Q_As.pdf . This is a real example of withdrawn Q&As (prospectus topic, not MiFID).
- Registers: Solr-based machine-to-machine. - "ESMA Registers system offers machine-to-machine (A2A) services ... ESMA Registers data is maintained through Solr indexes" - https://registers.esma.europa.eu/publication/helpApp . FIRDS full and delta files, XML (ISO 20022); instructions - https://www.esma.europa.eu/document/firds-instructions-access-and-download-full-and-delta-reference-data-files . FIRDS and the registers are instrument/entity data, not advice text; low relevance for a RAG compliance corpus. Daily cadence of FIRDS: UNVERIFIED on an official page in this round.
- ESMA news items announce Q&A updates, e.g. "New Q&As available" 27/06/2025 and 27/02/2026 with Q&A IDs (https://www.esma.europa.eu/press-news/esma-news/new-qas-available-26). Usable as a change feed. RSS URL: UNVERIFIED.

### Limits / gaps
- No numeric rate limit found for ESMA site or Registers. UNVERIFIED.
- Guidelines (MiFID II suitability, product governance, etc.): not fetched this round. UNVERIFIED. Same copyright notice applies.
- ESMA Q&A answers on EU-law interpretation are given by the Commission: "In case your question would require the interpretation of EU law, ESMA will forward your question to the European Commission to answer." - https://www.esma.europa.eu/publications-and-data/questions-answers

## 3. PRIIPs KIDs

### Confirms
- No central public database. - "there is not currently a central European database where KIDs are collected and stored. ... there is no single database for information about PRIIPs and KIDs." - ESAs advice on PRIIPs review https://www.eiopa.europa.eu/system/files/2022-04/esa_advice_on_the_review_of_the_priips_regulation.pdf (read 2026-11-01). The same text says ESMA's own research sample of 47,100 KIDs (2018 - July 2021) came partly from SRP.com (~30,900) and partly from manufacturer websites by web scraping (~16,200).
- Publication duty is on the manufacturer's website. - "the PRIIP manufacturer shall draw up for that product a key information document ... and shall publish the document on its website." (Art. 5(1)) - https://eur-lex.europa.eu/eli/reg/2014/1286/oj/eng ; Q&A 4: must be "on the public section of a website".
- Some Member States require ex ante notification (Art. 5(2)); example Italy, Consob SFTP + XML (https://www.consob.it/documents/1912911/1971607/KidPriipsOperatingInstructions.pdf/...). Not public bulk.
- Reform: "On 18 December 2025, the Council and the European Parliament agreed on an updated retail investment framework." (https://www.consilium.europa.eu/en/policies/retail-investment-strategy/). Parliament plenary indicative date 11 November 2026 (https://www.europarl.europa.eu/legislative-train/...file-retail-investment-strategy-key-information-document). Commission expects OJ publication "at the latest in January 2027" (call for advice, esma.europa.eu 2026-08). The ESAs recommended machine-readable KIDs. The KID template is likely to change; the corpus should tag KIDs with the regime date.

### Practical sourcing (fund houses)
- Xtrackers (DWS): KID list https://etf.dws.com/en-gb/information/etf-documents/kids/ ("413 Results" on the read day, includes UK KIIDs). PDFs per ISIN; PROBE: https://etf.dws.com/Download/PRIIPS%20KID/LU0411078552/DE/DE returned 200 PDF 100,190 B (German, DE jurisdiction); the same pattern with /EN and /FR returned 404 HTML (jurisdiction/language combos limited, URL pattern for EN UNVERIFIED). English LU KID found: https://etf.dws.com/en-lu/AssetDownload/Index/.../DWS-PRIIPSKID-LU0292095535-LU-en-2023-02-20-pdf.pdf . A KID states "key information is accurate as at 16.02.2026" - a date usable as version. Terms of use / automated access: DWS robots.txt disallows only /etfdata/* and /export/* (PROBE 2026-11-02); website terms of use UNVERIFIED.
- iShares: KIDs in EN and DE for the same fund (listed via Morningstar documents page, "PRIIP KID | English | Apr 9, 2026" and "German | Apr 9, 2026"), https://global.morningstar.com/en-eu/investments/etfs/0P0001OWZT/documents ; iShares library https://www.ishares.com/uk/individual/en/library (KIDs registered by country). Terms UNVERIFIED.
- Deutsche Bank PRIIPs KID repository by identifier, language and jurisdiction: https://www.priips.db.com/ (structured products, EN + DE shown). Terms UNVERIFIED.
- Terms for reuse: KIDs are manufacturers' documents. No open licence found on any of these pages; treat as "published for investors", reuse in a product = ask the manufacturer or limit to demo with attribution. UNVERIFIED legal position; needs counsel.
- Tables: KID has the performance scenarios table and the costs-over-time / composition-of-costs tables (RTS 2017/653 Annexes IV-VII as amended). Table extraction from the DWS PDF was not run (pdftotext not installed locally).

## 4. UK FCA Handbook (handbook.fca.org.uk)

### Confirms
- Handbook T&C: OGL v3.0 with FCA credit. - "You may use the information on the Site or the API in accordance with the terms of the Open Government Licence v3.0." and "The source of Our material should be acknowledged in all copies, either by appropriate words or by adding the FCA copyright symbol (i.e. (c) FCA)." (clauses 25-26) - https://handbook.fca.org.uk/footer-widget/terms-and-conditions (read 2026-11-01).
- Mixed provenance. - "The Site includes material: re-used or adapted under the Open Government Licence v 3.0; re-used or adapted from EUR-Lex under the Creative Commons Attribution 4.0 ...; and drafted using material downloaded from the website of the European Securities and Markets Authority ... under the terms of ESMA's copyright notice." (clause 23)
- Definitive text. - "The definitive version of FCA Handbook text at any particular time is the version contained in the Instruments published on this Site." (clause 27)
- CONFLICT (important): the main FCA site terms are restrictive. - "You must not reproduce or store any part of this site in any other website or include it in any public or private electronic retrieval system or service without our prior written permission." (clause 3.3) - https://www.fca.org.uk/legal (last updated 12/10/2026, read 2026-11-01). The same page says "Content from the FCA Handbook can be reproduced and adapted in accordance with the Open Government Licence v3.0 and our Handbook Terms and Conditions." So Handbook = OGL; other fca.org.uk pages (policy statements, Handbook Notices, guidance) = restrictive terms; ask the FCA or restrict. A separate page says "If you would like to reproduce content from the Handbook you will need to apply for a Handbook licence agreement." (https://www.fca.org.uk/handbook-licence-agreement, last updated 17/08/2026). The docs conflict on whether a licence agreement is needed beyond OGL. Treat as UNRESOLVED; email Handbookfeedback@fca.org.uk.
- Handbook API (new). - "Access to FCA Handbook data is now available directly through our new API" - https://www.fca.org.uk/news/blogs/making-compliance-simpler-opening-fca-handbook-new-api (2026-06-08). Portal https://handbook.fca.org.uk/handbook-api ("Sign in required"). Free account: "The Handbook API is available to all users who have registered for a free account on the website." Provides "Handbook, Technical Standards and Glossary data". - https://handbook.fca.org.uk/guides/faq (read 2026-11-01)
- API has no history. - "No. The API does not provide past versions of Handbook content. Attempting to extract information from a past date using the API will return an error message. Only current and future editions will be available." - FAQ. Rate limit not quantified. - "Protected endpoints are rate-limited per authenticated user and endpoint path." - FAQ.
- Revocation risk. - "We shall have the right at any time upon notice to You to revoke Your access to the API. ... You shall at Our request immediately delete all copies of the API and/or the API Data" (clause 13). Ingesting through the API therefore carries a deletion duty; ingestion of the website HTML under OGL does not (analysis, not a quote). Derived Data belongs to the user (clause 19).
- Point-in-time on the website: timeline. - "view the Handbook as it existed on any date in the past or the future, including how to use our 'track changes' functionality." (FAQ) and "Enter a date between 1 January 2001 and 31 December 2004 ... list of PDF files that constitute the Handbook archive." - https://handbook.fca.org.uk/guides/timeline-guide (read 2026-11-01). Date is in the URL; versions are per chapter/section.
- Update cadence: "The FCA Board normally meets at least 10 times a year to approve legal instruments." Change detection: monthly mailing list on account creation; instruments published alongside "a corresponding policy statement or Handbook Notice". Handbook tree shows "Last modified" and "Recent changes" columns. No RSS/XML bulk found. - FAQ and timeline guide.
- Language: English only (inference). Jurisdiction: UK. Formats: HTML, PDF (archive), JSON via API (format UNVERIFIED).
- Size: COBS alone not measured. UNVERIFIED; measure by crawling /handbook/COBS/ in the build.

## 5. FCA Financial Services Register API

- Registration: free self-serve at https://register.fca.org.uk/Developer/s/ (login-walled; page content not readable anonymously). - "you can sign up to the FS Register API Developer Portal. This service, currently free of charge, allows users to generate a unique key" - https://www.fca.org.uk/firms/financial-services-register (read 2026-11-01)
- No SLA. - "As the API is a free service, we do not offer any service-level agreements (SLAs) or guarantees for uptime or issue resolution." - same URL.
- Rate limit from an FCA document: "The current rate limit is 50 requests per 10 seconds." and "designed for individual look-ups rather than bulk data access. It currently supports queries for one entity at a time" - http://www.fca.org.uk/publication/documents/register-extract-handbook.pdf (read 2026-11-01; date of document UNVERIFIED). Headers X-Auth-Email and X-Auth-Key, base https://register.fca.org.uk/services/V0.1 (community client docs, financial-services-register-api.readthedocs.io; secondary source). 429 on breach (secondary source).
- Data: firms (FRN), individuals (IRN), funds (PRN), Search endpoint. Bulk: paid Register Extract Service (RES) or one-off data cut.
- Terms of use for the data: not read (portal). UNVERIFIED.
- Relevance: entity data, not text. Low value for RAG retrieval; useful only for "is this firm authorised" metadata demos.
- Separate FCA FIRDS/FITRS data API: https://api.data.fca.org.uk (anonymous file listing, per community catalogue 2026-07-25; secondary, UNVERIFIED).

## 6. legislation.gov.uk

### Confirms
- Licence. - "All content on legislation.gov.uk ... is available under the Open Government Licence v3.0. ... exploit our content commercially and non-commercially" with suggested attribution "(c) Crown and database right. Derived from content available under the Open Government Licence v3.0 from legislation.gov.uk." - https://legislation.github.io/data-documentation/reuse-licence.html (read 2026-11-01). Dual licensing: "Legislation originating from the EU is available for re-use under the terms of the Commission Decision 2011/833/EU." Some content is derived from Westlaw with its own attribution.
- Onshored EU acts are present as eur/YYYY/N. PROBE 2026-11-02 (data.xml, UA header): eur/2014/1286 (200, 53 KB), eur/2017/565 (200, 136 KB), eur/2017/653 (200, 194 KB), eur/2014/600 (first call timed out; later data.xml with point in time 2018-01-03 returned 200, 656 KB; data.htm 200, 1.29 MB). Also uksi/2017/701 (MiFID regs 2017, 200, 1.18 MB, 20 versions listed).
- Titles carry "(revoked)" for the UK PRIIPs Regulation, 2017/565 and 2017/653 (PROBE titles: "... (PRIIPs) (Text with EEA relevance) (revoked)"). This is a ready-made repeal/withdrawal case. The reason and revocation date were not read: UNVERIFIED (likely replaced by FCA rules, not verified).
- Versions: `<atom:link rel="http://purl.org/dc/terms/hasVersion">` lists point-in-time dates (e.g. PRIIPs Reg: 2014-11-26, 2014-12-29, 2016-12-24 ... 12 entries; 2017/653: 8 entries; 2017/565: 17). Point-in-time URL: `/eur/2014/600/2018-01-03/data.xml`. - "When an entire piece of legislation is requested using a URL that contains a version such as .../ukpga/1985/67/2003-04-01 ... A URL without a date will give you the current version" - https://www.legislation.gov.uk/developer/formats/xml (read 2026-11-01). Status attributes: "Prospective, Repealed or Discarded".
- Formats: XML (CLML), HTML, PDF (some), RDF; Atom feeds via /data.feed; SPARQL at https://www.legislation.gov.uk/sparql. - https://legislation.github.io/data-documentation/api/overview.html
- Change detection: "Use the New Legislation feed ... Use the Publication Log feed if you are interested in extracting any kind of new or updated content, including updates to legislation or resources already published." - https://www.legislation.gov.uk/fair-use-policy. PROBE 2026-11-02: https://www.legislation.gov.uk/update/data.feed returns the Publication Log (updated 2026-11-02); /new/data.feed returns the new-legislation feed. Effects feed: https://www.legislation.gov.uk/changes/affected/{type}/{year}/{number}. Per-item `dc:modified` in the XML (PRIIPs Reg 2026-04-14; 2017/565 2025-10-22).
- Languages: English (dc:language en); some items have Welsh versions (not checked).

### Limits and conflict
- CONFLICT on rate limit. https://www.legislation.gov.uk/fair-use-policy: "You must not exceed the request rate limit of 1,500 requests in any 5-minute period." https://legislation.github.io/data-documentation/fair-use.html and the API overview: "3,000 requests in any 5 minute period" / "limit each IP address to 3,000 API requests every 5 minutes." Use the stricter 1,500/5 min until resolved. A user agent is mandatory ("they must specify a user agent"). 403 on exceeding. Breaching can result in blocking.
- "We recommend avoiding requesting entire items of legislation" for very large items (XML formats page).
- Bulk: no bulk dump found; the docs encourage crawling inside the fair-use limit: "We encourage users to use our API in their own applications, including crawling and bulk access".

## Proposed smallest EU+UK subset

Goal: >1 language, several versions, withdrawal/delete, tables. About 12 items, ~25 MB raw.
1. Multilingual + versions (EUR-Lex/CELLAR): PRIIPs Regulation 1286/2014 consolidated versions 02014R1286-20141229, -20190801 (or -20211221), -20240109, each in EN + DE + FR XHTML (3 versions x 3 languages = 9 files, ~0.5-1 MB each, size by analogy to the MiFID II probe). PRIIPs is short, so the cost is low. Add MiFID II 02014L0065 EN+DE for 2 versions (20230323, 20250117) only if more volume is needed (~1 MB per file).
2. Updates: the same consolidated series (new CELEX per amendment), plus one corrigendum (for example 32014R1286R(01)) to test corrigenda handling.
3. Withdrawn/deleted: (a) UK onshored PRIIPs Regulation eur/2014/1286, marked "(revoked)", with its 12 point-in-time versions (take 3); (b) ESMA PRIIPs/prospectus Q&A items marked "Deleted" in the "Overview of changes made to the Prospectus Q&As" (not MiFID, but a documented list) or the JC PRIIPs Q&A snapshots 21 December 2022 vs 5 December 2025 (diff shows revised/deleted answers, since the 2022 text states which were revised or deleted); (c) ESMA investor-protection Q&A PDF frozen 15 December 2023 vs the Q&A tool items from 2024 on (supersession by source).
4. Tables: RTS 2017/653 consolidated (02017R0653-20230101) Annexes (SRI, performance and cost tables) in Formex/XHTML, plus 2-3 KIDs from two fund houses (iShares EN+DE for one fund, DWS DE for one ISIN with a second language if found). The KID PDFs hold the real cost tables; terms are UNVERIFIED so limit to internal testing.
5. UK text: FCA Handbook COBS 9A (suitability) and COBS 6 (disclosure) from the website under OGL, two timeline dates (one before and one after a recent instrument). The Handbook API gives only current/future versions, so points in time need the website timeline.
6. Optional: ESMA Q&A section "Information on costs and charges" (updated 15 December 2023) as a PDF section; ESMA copyright requires the "drafted using material downloaded from ESMA's website" disclaimer if transformed.

Change-detection test plan: (i) CELLAR lastModificationDate poll by SPARQL for the 5 acts, (ii) legislation.gov.uk /update feed filtered on the three eur items, (iii) FCA Handbook monthly email (manual) + Last modified column, (iv) ESMA "New Q&As available" news and the Q&A tool.

## Improvements
- Make the corpus store per-document licence and attribution (CC BY 4.0, OGL v3.0 with (c) FCA, ESMA transformed-text disclaimer, KID = unknown).
- Mark consolidated EU text "not authentic" and carry the OJ CELEX of the base act.
- Prefer CELLAR REST + SPARQL over the SOAP service for ingestion (no registration, no 10,000 cap); poll lastModificationDate.
- Do not ingest through the FCA Handbook API if the product must keep data after revocation; use the website under OGL, and ask the FCA about the "Handbook licence agreement" wording.
- Keep non-Handbook fca.org.uk content (Handbook Notices, policy statements) out of the corpus until permission is clear.
- Use the stricter 1,500 requests/5 min on legislation.gov.uk and send a user agent.

## Gaps
- Official page for ESMA guidelines and for FIRDS cadence not read. ESMA RSS URL not found.
- Q&A tool export/API and withdrawal status labels not verified; "rejected" list exists.
- CELLAR rate limits, Data Dump size, and RSS registration: not documented in the pages read.
- KID manufacturer website terms (DWS, iShares, Deutsche Bank): not read. KID table extraction not tested.
- FCA Register API terms and developer portal docs login-walled; rate limit comes from an FCA PDF of unknown date.
- Reason/date for UK revocation of the PRIIPs acts not read; meaning of the second end-of-validity date for 2017/653 unclear; the effective date of Delegated Reg 2021/2268 differs between sources.
- FCA Handbook size for COBS not measured; Handbook API format not seen (login).
