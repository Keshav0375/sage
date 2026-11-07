# D - Google Cloud Model Armor (extract, fetched 2026-11-02)
Quotes copied from raw page text (curl, tags stripped). Page "Last updated" lines as shown.

URLs and last-updated:
- Overview https://docs.cloud.google.com/model-armor/overview : Last updated 2026-10-26 UTC.
- Quotas https://docs.cloud.google.com/model-armor/quotas : Last updated 2026-10-28 UTC.
- Templates (manage) https://docs.cloud.google.com/model-armor/manage-templates : Last updated 2026-10-29 UTC.
- Sanitize https://docs.cloud.google.com/model-armor/sanitize-prompts-responses : Last updated 2026-11-02 UTC.
- Locations https://docs.cloud.google.com/model-armor/locations : no date captured.
- SCC pricing https://cloud.google.com/security-command-center/pricing (section "Possible indirect charges associated with Model Armor") : no date shown.
- Product page https://cloud.google.com/security/products/model-armor#pricing : no date.
- Note: /model-armor/pricing, /model-armor-pricing, /templates-overview, /filters-overview returned 404. Overview links pricing to the two cloud.google.com pages above.

## 1. Filters and confidence levels (Overview)
- RAI: "You can screen prompts and responses at the specified confidence levels for the following categories:" Hate speech; Harassment; Sexually explicit; Dangerous content; CSAM.
- CSAM: "Contains references to child sexual abuse material (CSAM). This filter is applied by default and cannot be turned off."
- PI/jailbreak: "When prompt injection and jailbreak detection is enabled, Model Armor scans prompts and responses for malicious content. If detected, Model Armor blocks the prompt or response."
- "For prompt injection and jailbreak detection, if the word count is fewer than three words, Model Armor returns NO_MATCH_FOUND because such inputs lack enough information to constitute an attack."
- Malicious URI: "When malicious URL detection is enabled, Model Armor scans URLs to identify whether they're malicious." / "Model Armor extracts URLs until it reaches 256 URLs or the end of the payload, and scans only the first 256 URLs found in prompts and responses."
- SDP: "Sensitive Data Protection is a Google Cloud service that helps you discover, classify, and de-identify sensitive data."
- Confidence: "High: Identifies content with a high likelihood of violation. Medium and above: Identifies content with a medium or high likelihood of violation. Low and above: Identifies content with a low, medium, or high likelihood of violation."
- "You can set confidence levels only for prompt injection and jailbreak detection and responsible AI safety filters."
- "Confidence levels for Sensitive Data Protection operate differently from those for other filters." (SDP uses match likelihood.)
- Guidance: "for both prompt injection and jailbreak detection and general content safety (hate speech, harassment, dangerous content), start with High or Medium and above to minimize false positives." Also "Set prompt injection and jailbreak detection filters to Medium. For applications like Gemini Enterprise, set the threshold to High".

## 2. Input types, languages
- Documents (Overview, Document screening): "Model Armor can screen the following types of documents for safety, prompt injection and jailbreak attempts, sensitive data, and malicious URLs: PDFs; CSV; Text files: TXT; Microsoft Word documents: DOCX, DOCM, DOTX, DOTM; Microsoft PowerPoint slides: PPTX, PPTM, POTX, POTM, POT; Microsoft Excel sheets: XLSX, XLSM, XLTX, XLTM"
- "Supported files are limited to 4 MB in size. If a file exceeds this limit, Model Armor skips scanning the file."
- "Text extracted from supported files is subject to the token system limits. Model Armor rejects requests to scan files that are smaller than 69 bytes and returns an InvalidDocumentInputException error"
- Sanitize API, File-based prompts: "To sanitize a prompt that is stored in a file, provide the file content in base64 format. Model Armor doesn't automatically detect the file type. You must explicitly set the byteDataType field ... The possible byteDataType values are PLAINTEXT_UTF8, PDF, WORD_DOCUMENT, EXCEL_DOCUMENT, POWERPOINT_DOCUMENT, TXT, and CSV."
- "Sensitive Data Protection de-identification is not supported for file-based prompts."
- Limitations: "Model Armor doesn't decode or inspect encoded content, such as prompts encoded in Base64, hexadecimal, URL encoding, or ciphertext." / "Model Armor doesn't support audio or video." / "Model Armor inspects each prompt and response independently as a single-turn request. It doesn't track conversation history"
- Images (Preview): "Model Armor screens images only in the JPEG, PNG, and BMP formats. Each image must be 4 MB or smaller." "Image screening is supported only in the us and eu multi-regions." "Model Armor doesn't support prompts that combine text and images in a single request."
- Languages: "The responsible AI and prompt injection and jailbreak detection filters are tested on the following languages: Chinese (Mandarin) English French German Italian Japanese Korean Portuguese Spanish. These filters can work in many other languages, but the quality of results might vary." / "The Sensitive Data Protection filter supports English and other languages depending on the infoTypes that you selected."
- Multi-language flag: "Enable multi-language detection on a per-request basis by setting the enableMultiLanguageDetection flag to true" ; "In regions with limited multi-language detection support (asia-south1 and northamerica-northeast2), if you send non-English content to detectors like prompt injection and jailbreak or RAI, Model Armor returns a verdict of Skipped Detection"
- Sanitize: "Don't include system prompts: The system prompt shouldn't be included in the userPromptData field."

## 3. Limits, quotas, regions, SLA (Quotas page)
- "API queries | 1200 queries per minute (QPM) per project"; "Requests to ExternalProcessor | 600 QPM per project". "You can apply a value between 0 to 1,200 QPM per project." "If you need more than the default quota, contact Cloud Customer Care."
- "Model Armor screens text up to 65,536 tokens (approximately 262,144 characters) for prompt injection and jailbreak detection, responsible AI, and child sexual abuse material (CSAM) filters."
- Table: PI/jailbreak 65,536; RAI 65,536; CSAM 65,536; "Sensitive Data Protection 130,000 (0.5 MB)".
- "If the prompt or response exceeds the filter's token limit, the filter returns EXECUTION_SKIPPED and includes Detection skipped as token limit exceeded." (fail-open per filter; caller must check.)
- "When you sanitize streaming text in real-time mode, Model Armor supports unlimited tokens. In contrast, buffered streaming mode is subject to the token limits"
- "These token limits don't apply to the Model Armor integration with Gemini Enterprise."
- Files/images: "All supported files and images | 4 MB".
- Exclusion rules (Preview): max 10 rule sets, 10 rules/set, 10 dictionaries, 128 KB word list, 1,000-char regex, 130,000 tokens (0.5 MB) scanned.
- Regions (Locations): Asia Pacific asia-northeast1, asia-northeast3, asia-south1, asia-southeast1, australia-southeast2; N. America northamerica-northeast2, us-central1, us-east1, us-east4, us-west1; S. America southamerica-east1; Europe europe-southwest1, europe-west1, europe-west2, europe-west3, europe-west4, europe-west9; multi-regions "eu" and "us".
- "Feature availability varies by region to comply with data residency and other regional requirements."
- Endpoint: regional "modelarmor.LOCATION.rep.googleapis.com". Overview: "To access Model Armor regional endpoints from within a VPC network, you must create a Private Service Connect endpoint".
- SLA: NOT FOUND (no SLA/uptime text on overview, quotas, locations, sanitize pages; product page not found to state one).

## 4. Pricing (SCC pricing page; overview "Pricing")
- Overview: "Model Armor can be purchased as a standalone service or as an integrated part of Security Command Center. You aren't charged for data that is skipped."
- "Model Armor uses the total number of tokens in AI prompts and responses for pricing purposes."
- "Model Armor uses the same token definition as Gemini Enterprise Agent Platform: four characters (using UTF-8 code points) per token excluding white space."
- Standalone: "there is no cost for using Model Armor up to 2 million tokens per month. Use of Model Armor beyond this no-cost monthly allocation is billed at a rate of $0.10 per million tokens."
- "When Sensitive Data Protection is enabled within Model Armor, there are no additional charges to use it."
- SCC table (tokens free/month; cost per additional 1M): Enterprise subscription 3 billion, $0.10; Premium subscription 3 billion, $0.10; Premium activated at organization level 2 million, $0.10; Premium activated at project level 2 million, $0.10.
- "Model Armor is included in Security Command Center Enterprise and Premium tiers."
- Not included in Model Armor price: Cloud Logging ingestion/storage is separate (SCC page: "Any costs associated with the ingestion and storage of log data").

## 5. Latency
- NOT FOUND as a figure on overview, quotas, sanitize, templates pages. Only qualitative: streaming methods "are particularly useful for applications that handle large text payloads or that require low-latency interactions with LLMs."

## 6. SDP basic vs advanced; detect vs de-identify; standalone; GA/preview
- Basic: "Basic configuration only supports inspection operations and doesn't support the use of Sensitive Data Protection templates." Categories: "Credit card number; US social security number (SSN); Financial account number; US individual taxpayer identification number (ITIN); Google Cloud credentials; Google Cloud API key"
- Advanced: "Advanced configuration supports both inspection and de-identification operations." "Advanced: A more configurable option that uses templates defined in Sensitive Data Protection to inspect or de-identify sensitive data." Needs Inspect template (projects/P/locations/L/inspectTemplates/ID) and optional De-identify template (.../deidentifyTemplates/ID); cross-project needs roles/dlp.user and roles/dlp.reader.
- "basic Sensitive Data Protection provides limited infotypes, mainly addressed to the US region." / "Use advanced Sensitive Data Protection template to configure the required infotypes for your use case"
- De-identify limits: not supported for file-based prompts; "Model Armor streaming methods don't support Sensitive Data Protection de-identification."
- Enforcement: "Inspect only: ... logs the details to Cloud Logging ... doesn't stop the request"; "Inspect and block: ... prevents the offending content from proceeding." "The calling service ... Policy Enforcement Point (PEP) is responsible for blocking the further processing."
- Standalone / non-Vertex: "Whether you are deploying AI in Google Cloud or other cloud providers, Model Armor can help you prevent malicious input, verify content safety, protect sensitive data..." Sanitize API is model-agnostic REST (SanitizeUserPrompt, SanitizeModelResponse; caller sends text and gets verdict); page does not say "works with any model" in those words. Sanitize usage: "Intercept prompt injection attacks, jailbreak attempts, and sensitive data before sending inputs to language models or AI agents" (per fetch summary of sanitize page; not re-verified verbatim).
- Data handling: "Model Armor operates as a stateless service, processing all prompts and model responses entirely in memory."; SOC 1/2/3 and ISO/IEC 27001 mentioned.
- GA/Preview labels seen: Image screening = Preview ("Pre-GA features are available "as is" and might have limited support."); exclusion rules = Preview; prompts with an exclusion rule = Preview; streaming exclusion = Preview. Text prompt/response sanitize, document screening, SDP basic/advanced, PI/jailbreak, RAI, malicious URI, CSAM: no Preview label on the pages, but pages do not explicitly say "GA" either (treat as unlabelled, i.e. presumably GA; GA statement itself NOT FOUND). Release notes page not fetched.
