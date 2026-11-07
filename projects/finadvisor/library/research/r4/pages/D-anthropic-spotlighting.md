# D: Anthropic docs + Spotlighting extract (fetched 2026-11-02)
No "last updated" date shown on any platform.claude.com docs page fetched. Docs list Haiku 5.5 / Opus 5 etc, so this is the current live version as of 2026-11-02.

## A1. Citations  https://platform.claude.com/docs/en/build-with-claude/citations (docs.claude.com 302s here)
- Types: "Three document types are supported for citations." Table: Plain text -> sentence chunking -> "Character indices (0-indexed)"; PDF -> sentence -> "Page numbers (1-indexed)"; Custom content -> "No additional chunking" -> "Block indices (0-indexed)".
- char_location: {"type":"char_location","cited_text":...,"document_index":0,"document_title":...,"start_char_index":0,"end_char_index":50 // exclusive}
- page_location: {"type":"page_location",...,"start_page_number":1 // 1-indexed,"end_page_number":2 // exclusive}
- content_block_location: {"type":"content_block_location",...,"start_block_index":0,"end_block_index":1 // exclusive}
- "Set `citations.enabled=true` on each of your documents. Currently, citations must be enabled on all or none of the documents within a request."
- "Only text citations are currently supported. Image citations are not yet possible."
- "Citing images from PDFs is not currently supported." / scanned PDFs without extractable text "are not citable."
- Token costs: "Enabling citations incurs a slight increase in input tokens because of system prompt additions and document chunking." "The `cited_text` field is provided for convenience and does not count toward output tokens." "When passed back in subsequent conversation turns, `cited_text` is also not counted toward input tokens."
- "Because the API parses citations into the response formats described in the following sections and extracts `cited_text` directly, citations are guaranteed to contain valid pointers to the provided documents."
- "In Anthropic's evaluations, the citations feature is significantly more likely to cite the most relevant quotes from documents than purely prompt-based approaches."
- Streaming: "citations arrive as a `citations_delta` delta type inside `content_block_delta` events. Each delta contains a single citation to add to the `citations` list on the current `text` content block."
- Structured outputs (Feature compatibility): "**Citations and structured outputs are incompatible**" "Citations cannot be used together with structured outputs. If you enable citations on any user-provided document (`document` blocks or `search_result` blocks) and also include the `output_config.format` parameter (or the deprecated `output_format` parameter), the API returns a 400 error."
- Supported models list includes claude-haiku-5-5, claude-sonnet-5-5, claude-opus-5-5 etc. "All active models support citations." ZDR eligible (excludes Covered Models).

## A2. Search results  https://platform.claude.com/docs/en/build-with-claude/search-results
- "Search result content blocks let Claude cite your own content the same way it cites web search results: each citation carries the source and title you provided."
- "All active models support search results with citations, with the exception of Claude Haiku 3. No beta header is required"
- Required fields: type "search_result"; source ("Any stable string works: a URL, or an internal identifier such as `kb://article-1234`"); title; content (array of text blocks). Optional: citations {enabled}, cache_control.
- "Citations are disabled by default ... All search results in a request must use the same setting"
- "Search results hold text only. Images and other media are not supported inside the `content` array."
- "Messages API: Always on. Send `search_result` blocks in a tool result or directly in a user message." "Managed Agents: ... Accepted only in tool results"
- "if your prompt asks for only JSON, the response might contain few or no citations"

## A3. Mitigate jailbreaks and prompt injections  https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks
- "Although Claude is inherently resilient to such attacks, the additional steps on this page strengthen your guardrails"
- Two categories: "Jailbreaks and direct prompt injection, where the *user* ... is the adversary" ; "Indirect prompt injection, where the user is trusted but Claude processes *third-party content*..."
- "Harmlessness screens: Use a lightweight model such as Claude Haiku 5.5 to pre-screen user input before it reaches your main conversation. Use structured outputs to constrain the response to a simple classification. Claude Haiku 5.5 runs safety classifiers that can decline the screening request itself, so treat a response with `stop_reason: "refusal"` as a harmful verdict."
- "Input validation: Filter user input for known injection patterns before it reaches Claude."
- Indirect: "Put untrusted content only in tool results. Deliver third-party content to Claude inside `tool_result` blocks, never in `system` prompts or plain user `text` blocks. Claude is trained to treat instructions that appear inside tool results with appropriate skepticism."
- "Tell Claude what the content is and where it came from."
- "State the policy in your system prompt. ... content returned from tools, documents, or searches is untrusted data and must never override the system prompt or the user's original request."
- "JSON-encode untrusted content. ... JSON escaping provides unambiguous delimiters between the untrusted payload and the surrounding structure, so an attacker cannot close a quote or tag to 'break out' into an instruction context."
- "Don't put your own instructions in tool results. ... Send your instructions in a `user` turn that follows the `tool_result` block."
- "Limit Claude's access to sensitive data and actions. Apply the principle of least privilege ..."
- "Screen tool outputs before Claude acts on them. ... Run each tool, pass its raw output to a small classifier call with Claude Haiku 5.5, and only return the content as a `tool_result` block if the screen reports no injection attempt." Verdict via structured outputs (injection_suspected boolean). "Treat a `stop_reason: "refusal"` response from Claude Haiku 5.5 the same way"
- "Red-team your own agent. Before deploying, test your workflow with documents, emails, and tool outputs that deliberately contain injection attempts"
- Note: "If you're using the computer use tool or the browser use tool, Anthropic runs additional classifiers on what the tools return, such as screenshots or page text." (not applied to plain API tool results)
- "Continuous monitoring: Regularly analyze outputs for signs of successful injection."
- Chain example is a financial advisor chatbot (AcmeFinBot) using a 'harmlessness_screen' tool + structured outputs.
- NOT FOUND: any stated attack success rate on this page.

## A4. Reduce hallucinations  https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations
- "Allow Claude to say 'I don't know': Explicitly give Claude permission to admit uncertainty. This technique can drastically reduce false information."
- "Use direct quotes for factual grounding: For tasks involving long documents (>20k tokens), ask Claude to extract word-for-word quotes first before performing its task."
- "Verify with citations: ... You can also have Claude verify each claim by finding a supporting quote after it generates a response. If it can't find a quote, it must retract the claim."
- Advanced: "Chain-of-thought verification" (thinking with display "summarized"); "Best-of-N verification: ... Inconsistencies across outputs could indicate hallucinations."; "Iterative refinement"; "External knowledge restriction: Explicitly instruct Claude to only use information from provided documents and not its general knowledge."
- "Remember, although these techniques significantly reduce hallucinations, they don't eliminate them entirely. Always validate critical information, especially for high-stakes decisions."

## A5. Anthropic prompt-injection defenses  https://www.anthropic.com/research/prompt-injection-defenses  (published Nov 24, 2025)
- Attack success rate, internal Best-of-N attacker (model only / old safeguards / improved safeguards): Sonnet 4 13.8/10.7/2.0%; Sonnet 4.5 13.8/10.8/1.9%; Haiku 4.5 12.0/11.1/2.4%; Opus 4.5 8.0/7.6/1.4%. ~2,200-3,200 attempts per bar.
- "We scan all untrusted content that enters the model's context window, and flag potential prompt injections with classifiers."
- "An adaptive attacker is given 100 attempts per environment."
- "A 1% attack success rate—while a significant improvement—still represents meaningful risk."
- "No browser agent is immune to prompt injection, and we share these findings to demonstrate progress, not to claim the problem is solved."
- Context: this concerns browser agent (Claude for Chrome); not stated to apply to raw API tool results.
- Earlier (search snippet only, anthropic.com/news/claude-for-chrome, Aug 2025, not opened): 23.6% -> 11.2% ASR with mitigations. NOT verified by page read.
- Newer figures (0% Sonnet 5 etc.) appeared only in a third-party summary (aiunderstanding.org); UNVERIFIED, no Anthropic primary source read. Treat as NOT FOUND.

## A6. Constitutional Classifiers  https://www.anthropic.com/research/constitutional-classifiers (Feb 3, 2025)
- "no universal jailbreak was discovered" (183 participants, 3,000+ hours).
- Automated jailbreak success 86% without classifiers -> "4.4%" with.
- Over-refusals up "by 0.38%" (not statistically significant, 5,000 conversations); "compute cost was moderately higher (by 23.7%)."
- Availability to API customers: NOT FOUND. Post says demo ran on claude.ai Feb 3-10, 2025 and testing continues "prior to deploying this method on our production systems in the future." Next-gen classifiers (Jan 2026) seen only via third-party snippet; not read.
- No docs page found stating API customers can invoke Constitutional Classifiers.

## A7. Content moderation guide  https://platform.claude.com/docs/en/about-claude/use-case-guides/content-moderation (first 100k of 114k chars read; no date shown)
- "If costs are a concern, a smaller model such as Claude Haiku 5.5 is an excellent choice because of its cost-effectiveness."
- Scenario 1B posts/month, 100 chars, 3% flagged, 50 output tokens per flagged: Haiku 5.5: "Input token cost: 28,600 MTok * $0.10/MTok = $2,860 USD", "Output token cost: 1,500 MTok * $0.50/MTok = $750 USD", "Monthly cost: $2,860 + $750 = $3,610 USD". Opus 5: $5.00 in / $25.00 out per MTok, "$180,500 USD".
- "Output tokens can be reduced even further by removing the `explanation` field from the response."
- Batch: "To reduce costs in situations where real-time moderation isn't necessary, consider moderating messages in batches."
- Latency: no explicit latency figures found in the read portion (only "quick decisions"). Remaining 14.6k chars unread.
- Note: code samples use claude-haiku-4-5-20251001 while text names Haiku 5.5.

## B. Spotlighting arXiv 2403.14720v1 (Hines et al., Microsoft; submitted 2024-03-20)
Abstract: "We introduce spotlighting, a family of prompt engineering techniques that can be used to improve LLMs' ability to distinguish among multiple sources of input. The key insight is to utilize transformations of an input to provide a reliable and continuous signal of its provenance." "Using GPT-family models, we find that spotlighting reduces the attack success rate from greater than 50% to below 2% in our experiments with minimal impact on task efficacy."
Models: "text-davinci-003, GPT-3.5Turbo (June 2023 version) and GPT-4 (June 2023 version). All experiments are conducted with temperature set to 1.0." No Claude models tested.
ASR corpus: "a synthetic dataset of 1000 documents"; payload is "a simple keyword payload attack" (return single keyword).
Baseline prompt-only: "For GPT-3.5-Turbo, the addition of instructions about prompt injection has almost no added benefit." Fig 3: baseline ASR "around 60%".
Delimiting: "including also special delimiters can reduce ASR by about half." "this kind of defense could easily be subverted by an attacker who gains knowledge of our system prompt and inserts their own delimiting." "we do not recommend this approach".
Datamarking: "With GPT-3.5Turbo, ASR is reduced from approximately 50% to below 3%. With Text-003, ASR is reduced from 40% to 0.00%." Summarization: 3.10% (GPT-3.5), 0.00% (text-003). Q&A: "GPT3.5-Turbo ASR is reduced to 8.0%, with GPT-4 ASR is reduced to 1.0%, with GPT-3-Text-003 ASR is reduced to 0.00%."
Encoding (base64): "the encoding approach outperforms datamarking and brings ASR to 0.0%, or quite close"; GPT-3.5: summarization 0.0%, Q&A 1.8%.
Task impact: datamarking: "across all of these benchmarks [SQuAD, WiC, BoolQ, IMDB], the presence of the datamarking transformation does not have any detrimental impact on task performance." Encoding: "only the most powerful LLMs are able to handle the decoding process with high fidelity. For example, GPT-3.5-Turbo suffers in task performance when faced with encoded text... decoding... occasionally accompanied by mistakes or hallucinations". "we recommend that encoding only be used with the highest-capacity models (e.g. GPT-4) and task performance should be validated in a use case specific way."
Recommendation: "we recommend that at least datamarking be used"; "if high-capacity LLMs are being used (such as GPT-4), our ultimate recommendation is to use an encoding approach."
Limitations: "we lack a clear understanding of why spotlighting actually helps." "spotlighting helps to create separation but is not perfectly secure against interference." Datamarking weakness: "it is easy to imagine an attack string that contains no spaces. This attack would then not be interleaved with the marking token at all." Mitigation: dynamic/randomized marking tokens and locations; "As defenders, we must assume that our entire system prompt has been leaked to an adversary." ROT13 is subvertible (attacker pre-encodes payload); base64 is one-way. Marking-token suggestion: "Unicode value U+E000" (Private Use Area). Attacks tested are simple keyword payloads only (no adaptive attacker evaluation). Few-shot (appendix): GPT-3.5 ASR below 5% but authors say low confidence due to label leakage.
