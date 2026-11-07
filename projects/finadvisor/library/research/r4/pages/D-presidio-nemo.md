# D: Presidio + NeMo Guardrails (extracted 2026-11-02)
Note: WebFetch returns model-summarised text; quotes below are as returned, not raw page bytes.

## A. Presidio
Docs moved: microsoft.github.io/presidio -> data-privacy-stack.github.io/presidio -> https://presidio.dataprivacystack.org/ (301s). Old paths under microsoft.github.io 404 for some pages.
### PyPI (curl pypi.org JSON, 2026-11-02)
- presidio-analyzer 2.2.366, uploaded 2026-10-27, license MIT, requires_python "<3.15,>=3.11". presidio-anonymizer 2.2.366 same date, MIT, "<3.15,>=3.11".
- Core deps analyzer: spacy>=3.4.4, phonenumbers, regex, pydantic, pyyaml, tldextract, numpy. Extras: transformers, stanza, gliner, azure-ai-language, langextract, server.
- Latest is 2.2.366 (2.2.x line, patch-numbered by build).
### GitHub https://github.com/microsoft/presidio
- "An open-source framework for detecting, redacting, masking, and anonymizing sensitive data (PII)"; "MIT license". Release version/date not on page.
- "there is no guarantee that Presidio will find all sensitive information."
### Entities (https://presidio.dataprivacystack.org/supported_entities/)
- "Presidio contains predefined recognizers for PII entities."
- Global: CREDIT_CARD, CRYPTO, DATE_TIME, EMAIL_ADDRESS, IBAN_CODE, IP_ADDRESS, MAC_ADDRESS, NRP, LOCATION, PERSON, PHONE_NUMBER, MEDICAL_LICENSE, URL, UUID. PERSON/LOCATION/NRP = "Custom logic + context" (NER); CREDIT_CARD "Pattern match + checksum".
- Country-specific incl. US (US_SSN, US_ITIN, US_PASSPORT, US_BANK_NUMBER, US_DRIVER_LICENSE...), UK (UK_NHS, UK_NINO...), IN (IN_PAN, IN_AADHAAR, IN_GSTIN...), AU, SG, CA_SIN, DE, ES, IT, PL, KR, NG, PH, SE, ZA, TH, TR, FI.
- Medical entities need `transformers` extra, "uses the Medical-NER model by default".
### NLP engines (https://presidio.dataprivacystack.org/analyzer/nlp_engines/transformers/)
- "consists of a spaCy pipeline which encapsulates a Huggingface Transformers model"; example config `en_core_web_sm` + `StanfordAIMI/stanford-deidentifier-base`.
- Analyzer page: "loads the NLP module (spaCy model by default)". spaCy sm vs lg difference: NOT FOUND on fetched pages.
### Languages (.../analyzer/languages/)
- "In its default configuration, it contains recognizers and models for English." "Each recognizer can support one language." "regular expressions are language agnostic," while "the context words ... aren't."
### Performance / latency
- NOT FOUND (no latency numbers). Only: batch mode "allows for faster processing of large amounts of text." Links to a GPU Acceleration page (not read).
### Anonymizer (.../anonymizer/)
- replace "Replace the PII with desired value." (default <ENTITY_TYPE>); redact "Remove the PII completely from text."; mask "Replace the PII with a given character."; hash "Hashes the PII text using salted hashing for security." (sha256/sha512); encrypt "Encrypt the PII using a given key."; custom "Replace the PII with the result of the function executed on the PII."; keep "Preserver [sic] the PII unmodified."
- Deanonymize: "Deanonymizers are used to revert the anonymization operation. (e.g. to decrypt an encrypted text)." Operator decrypt: "Decrypt the encrypted PII in the text using the encryption key." Only reversible ops (encrypt).
### Custom recognizers (.../analyzer/adding_recognizers/)
- "For simple recognizers based on regular expressions or deny-lists, we can leverage the provided `PatternRecognizer`"; remote: "A remote recognizer is an `EntityRecognizer` object interacting with an external service."; code: "Create a new class based on `EntityRecognizer`." (implement load, analyze).
### Published recall/precision
- presidio-research (github.com/microsoft/presidio-research): NO numbers. Only "evaluate Presidio as a system, a NER model, or a specific PII recognizer for precision, recall, and error analysis"; "this is using the vanilla Presidio, and the results aren't very accurate."; "boost the f score in ~30%". Published recall/precision: NOT FOUND.

## B. NeMo Guardrails
### Version/licence/Python
- PyPI nemoguardrails 0.24.1 uploaded 2026-09-16, license Apache-2.0, requires_python "<3.14,>=3.10". Docs: "The latest released version is 0.24.1."; "Python 3.10, 3.11, 3.12 or 3.13."; "licensed under the Apache License, Version 2.0." (https://github.com/NVIDIA-NeMo/Guardrails README; docs index).
- Core deps (PyPI): aiohttp, fastembed, onnxruntime, httpx, jinja2, lark, numpy, pydantic>=2.5, pyyaml, rich, typer, prompt-toolkit, protobuf, simpleeval, nest-asyncio. Extras: sdd = presidio-analyzer/anonymizer>=2.2 (only python<3.13), jailbreak = yara-python, multilingual = fast-langdetect, eval, server, tracing, gcp, all.
### Rail types (https://docs.nvidia.com/nemo/guardrails/latest/about/rail-types.html)
- "The NeMo Guardrails library supports five main types of guardrails." input, dialog, retrieval, execution, output.
- "Input rails apply guardrails before the LLM is called by validating and sanitizing user inputs." "Retrieval rails filter and validate retrieved knowledge (documents and chunks)" "Dialog rails steer and constrain the multi-turn conversation" "Execution rails control and validate tool/function calls, their arguments, and results" "Output rails evaluate and post-process model responses"
- Use-case table: PII Detection = input, retrieval, output rails; Jailbreak Protection = input; Content Safety = input+output.
### Built-in rails
- Self-check input/output (guardrail-catalog/self-check.md): "The goal of the input self-checking rail is to determine if the input from the user should be allowed for further processing." LLM call; "a more comprehensive prompt like this uses more tokens and adds more latency."; single-call mode "helps reduce latency, it may result in lower quality."
- Jailbreak heuristics (jailbreak-protection.md): length-per-perplexity (threshold 89.79), prefix/suffix perplexity (1845.65), model gpt2-large; "IS NOT RECOMMENDED FOR PRODUCTION DEPLOYMENTS" in-process; "Jailbreak detection fails open."; supported on LLMRails not IORails. Also NemoGuard JailbreakDetect NIM tutorial.
- Latency of heuristics: "Docker 2057 ms (CPU) and 115 ms (GPU), and in-process 3227 ms (CPU) and 157 ms (GPU)."
- Injection detection: module nemoguardrails.library.injection_detection (actions, rail, rail_config, yara_config; extra `jailbreak` = yara-python). Behaviour description: NOT FOUND (page is a stub; catalog page 404).
- Presidio PII (third-party/presidio.md): "you must install Presidio and download the `en_core_web_lg` model for `spacy`."; install `pip install nemoguardrails[sdd]`; input/output/retrieval; detect (refuse) or mask flows; "The default value for this parameter is 0.2." (score threshold); "The retrieval flows run on `LLMRails` only". No latency guidance.
- Content safety (content-safety.md): Nemotron Content Safety, Meta Llama Guard 3, Google ShieldGemma; reasoning guards Nemotron Content Safety Reasoning, gpt-oss-safeguard; multilingual 9 languages; language detection "~12μs per request".
- Fact-check/hallucination (fact-checking.md): "grounded in the provided evidence"; hallucination "can be used when there are no supporting documents"; "performance ... strongly dependent on the capability of the LLM"; runs only on LLMRails.
### Stated latency / eval (evaluation/evaluate-guardrails.md, Nov 2023 numbers)
- Fact-check time per fact: gpt-3.5-turbo-instruct 188.8ms, gpt-3.5-turbo 435.1ms, gemini-1.0-pro 704.5ms, align_score-base 23.0ms, align_score-large 46.0ms.
- Llama Guard vs self-check accuracy: OpenAI Moderation 81.9% vs 65.9%; ToxicChat 94.4% vs 66.5%. Self-check input: "overly defensive behavior, with low precision and high recall".
- Hallucination rail: gpt-3.5-turbo 65% -> 90% intercepted.
- General rail overhead / "~0.5s" claim: NOT FOUND (README and overview contain none; source "does not report throughput or general rail overhead figures").
### Release notes 0.24.1 (no date on page)
- "Content-safety rails parse Nemotron 3.5 responses." "The server returns an overload response when IORails sheds a request through admission control." IORails = newer engine lacking dialog/retrieval/hallucination/jailbreak-heuristic flows.
