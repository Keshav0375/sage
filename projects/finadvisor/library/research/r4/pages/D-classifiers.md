# D-classifiers extract (fetched 2026-11-02)
Method: HF cards via hf_fs/exa where public; Meta cards via PurpleLlama raw GitHub MODEL_CARD.md (HF gated). HF API metadata (curl https://huggingface.co/api/models/<id>) for licence/params/lang of gated repos.

## 1. Llama Guard 4 12B
Source: https://raw.githubusercontent.com/meta-llama/PurpleLlama/main/Llama-Guard4/12B/MODEL_CARD.md (no date shown); HF API https://huggingface.co/api/models/meta-llama/Llama-Guard-4-12B (created 2025-04-23, lastModified 2025-04-29)
- Licence: HF API: "license: other" (tag license:other). Licence text itself NOT FOUND in card (UNVERIFIED which; do not assume).
- Params: "Llama Guard 4 is a natively multimodal safety classifier with 12 billion parameters trained jointly on text and multiple images." (Model Details). API safetensors total 12,001,097,216.
- Languages: "supporting English and multilingual text prompts (on the languages supported by Llama Guard 3) as well as mixed text-and-image prompts"; eval langs: "French, German, Hindi, Italian, Portuguese, Spanish, and Thai."
- Context length: NOT FOUND.
- Detects: "classify content in both LLM inputs (prompt classification) and in LLM responses (response classification)"; taxonomy S1-S14 MLCommons: Violent Crimes, Non-Violent Crimes, Sex-Related Crimes, Child Sexual Exploitation, Defamation, Specialized Advice, Privacy, Intellectual Property, Indiscriminate Weapons, Hate, Suicide & Self-Harm, Sexual Content, Elections, Code Interpreter Abuse (text only). Prompt injection/jailbreak: NOT covered; card: "as an LLM, Llama Guard 4 may be susceptible to adversarial attacks or prompt injection attacks ... see Prompt Guard 2 for detecting prompt attacks". S6 "Specialized Advice: Responses that contain specialized financial, medical, or legal advice" (relevant to FinAdvisor). PII: S7 Privacy "sensitive, nonpublic personal information".
- Metrics (in-house test set, output filtering, Classifier performance): English R 69% / FPR 11% / F1 61%; Multilingual R 43% / FPR 3% / F1 51%; Single-image R 41% FPR 9% F1 38%; Multi-image R 61% FPR 9% F1 52%. "We omit evals against competitor models". Latency: NOT FOUND.

## 2. Llama Prompt Guard 2 86M and 22M
Source: https://raw.githubusercontent.com/meta-llama/PurpleLlama/main/Llama-Prompt-Guard-2/86M/MODEL_CARD.md (identical text in /22M/MODEL_CARD.md); API created 2025-04-28
- Licence: HF API "license: other"; text NOT FOUND in card. Base models: "Both are open-source, MIT-licensed models from Microsoft."
- Params: 86M "Backbone Parameters 86M, mdeberta-v3"; 22M "22M, deberta-v3-xsmall". (API total incl. embeddings: 86M repo 278,810,882; 22M repo 70,830,722.)
- Languages: "Llama Prompt Guard 2 86M uses a multilingual base model and is trained to detect both English and non-English injections and jailbreaks. Both Prompt Guard 2 models have been evaluated for attack detection in English, French, German, Hindi, Italian, Portuguese, Spanish, and Thai." Limitation: "There is no version of deberta-xsmall with multilingual pretraining available. This results in a larger performance gap between the 22M and 86M models on multilingual data."
- Context: "Both Llama Prompt Guard 2 models support a 512-token context window. For longer inputs, split prompts into segments and scan them in parallel"
- Detects: "Both Llama Prompt Guard 2 models detect both prompt injection and jailbreaking attacks"; "classify prompts as 'malicious' if the prompt explicitly attempts to override prior instructions embedded into or seen by an LLM"; "No injection sub-labels: Unlike with Prompt Guard 1, we don't include a specific 'injection' label to detect prompts that may cause unintentional instruction-following." Binary benign/malicious. Prompt injection definition: "manipulate untrusted third-party and user data in the context window" (indirect-injection framing). Limitation: "adversaries may develop sophisticated attacks specifically to bypass detection."
- Metrics (private benchmark): table "AUC (English) | Recall @ 1% FPR (English) | AUC (Multilingual) | Latency per classification (A100 GPU, 512 tokens)":
  - PG1: .987 | 21.2% | .983 | 92.4 ms
  - PG2 86M: .998 | 97.5% | .995 | 92.4 ms
  - PG2 22M: .995 | 88.7% | .942 | 19.3 ms
  - "Llama Prompt Guard 2 22M reduces latency and compute costs by 75%, with minimal performance trade-offs."
  - AgentDojo "APR @ 3% utility reduction": PG1 67.6%, PG2 86M 81.2%, PG2 22M 78.4%, ProtectAI 22.2%, Deepset 13.5%, LLM Warden 12.9%.

## 3. protectai/deberta-v3-base-prompt-injection-v2
Source: https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2 (README via hf_fs; no date in card; citation year 2024)
- Status: "> **THIS PROJECT HAS BEEN ARCHIVED.** This project and its associated code on GitHub are no longer under active development or maintained."
- Licence: "License: Apache License 2.0"
- Params: NOT FOUND in card (base microsoft/deberta-v3-base).
- Languages: "Language(s) (NLP): English"
- Context: card code uses "truncation=True, max_length=512"; no explicit model context statement.
- Detects: "specifically developed to detect and classify prompt injection attacks"; "classifies inputs into benign (0) and injection-detected (1)". Limits: "It does not detect jailbreak attacks or handle non-English prompts"; "we do not recommend using this scanner for system prompts, as it produces false-positives."
- Metrics: eval set: Loss 0.0036, Accuracy 99.93%, Recall 99.94%, Precision 99.92%, F1 99.93%. "Post-Training Evaluation: Tested on 20,000 prompts from untrained datasets - Accuracy: 95.25% Precision: 91.59% Recall: 99.74% F1 Score: 95.49%". v1: Accuracy 94.8%, Precision 90.9%, Recall 99.6%, F1 95%. (Precision 91.59% implies roughly 8% of flagged are false positives; FPR NOT FOUND.) Latency NOT FOUND.

## 4. ibm-granite Granite Guardian (newest)
Newest per hf listing (updated_at): ibm-granite/granitelib-guardian-r1.0 (2026-10-16, LoRA adapter library) and ibm-granite/granite-guardian-4.1-8b (2026-08-27; "Release Date: April, 2026").
URLs: https://huggingface.co/ibm-granite/granite-guardian-4.1-8b ; https://huggingface.co/ibm-granite/granitelib-guardian-r1.0
### 4a granite-guardian-4.1-8b
- Licence: "License: Apache 2.0"
- Params: name 8B; "fine-tuned from ibm-granite/granite-4.1-8b". Exact count NOT FOUND in card.
- Languages: front matter "language: en" only.
- Context: card example "max_model_len=8192"; config.json max_position_embeddings 131072 (raw config, not card claim).
- Detects: "judge if the input prompts and the output responses of an LLM-based system meet specified criteria. The model comes pre-baked with certain criteria including but not limited to: jailbreak attempts, profanity, and hallucinations related to tool calls and retrieval augmented generation". Pre-baked: Harm (Social Bias, Jailbreaking, Violence, Profanity, Unethical Behavior), Context Relevance, Groundedness, Answer Relevance, Function Calling Hallucination; BYOC. Card example 3 uses a custom criterion for PII (SSN): "User message contains personal information or sensitive personal information" -> no built-in PII criterion. Indirect injection: NOT FOUND (only "Jailbreaking").
- Metrics: OOD safety aggregate F1 4.1-8b non-think 0.79, think 0.78 (3.3-8b non-think 0.81). Toxic Chat 0.78, HarmBench Prompt 0.78 (non-think). LM-AggreFact avg BAcc 0.760 / 0.764. FC Reward Bench BAcc 0.79 / 0.78. IFEval multi-constraint BAcc 0.844 (no-think). Latency numeric NOT FOUND ("non-thinking mode (low-latency yes/no judgements)").
### 4b granitelib-guardian-r1.0
- Licence: "license: apache-2.0"; language en; LoRA adapters for granite-4.0-micro, granite-4.1-3b/8b/30b.
- "Guardian Core: A LoRA adapter trained to judge whether the input prompts and output responses ... meet specified criteria, including safety risks (harm, jailbreaking, profanity, violence, sexual content, social bias, unethical behavior), hallucinations related to tool/function calls, and retrieval-augmented generation (RAG)". Output JSON `score` "yes"/"no". Metrics/context/params: NOT FOUND in top-level README (sub-readmes not fetched).

## 5. Qwen/Qwen3Guard-Gen-0.6B
Source: https://huggingface.co/Qwen/Qwen3Guard-Gen-0.6B (README via hf_fs; tech report arXiv:2510.14276, 2025)
- Licence: "license: apache-2.0"
- Params: 0.6B (name; base Qwen/Qwen3-0.6B). "trained on a dataset of 1.19 million prompts and responses labeled for safety"
- Languages: "Qwen3Guard-Gen supports 119 languages and dialects"
- Context: serve examples "--context-length 32768" / "--max-model-len 32768" (deploy setting, not stated as model limit).
- Detects: categories "Violent, Non-violent Illegal Acts, Sexual Content or Sexual Acts, Personally Identifiable Information, Suicide & Self-Harm, Unethical Acts, Politically Sensitive Topics, Copyright Violation, Jailbreak (Only for input)"; "Jailbreak: Content that explicitly attempts to override the model's system prompt or model conditioning." Severity: "safe, controversial, and unsafe". Indirect injection: NOT FOUND.
- Metrics: "achieves state-of-the-art performance on various safety benchmarks" (claim; numbers only in image performance.png). Numeric NOT FOUND in text. Latency NOT FOUND.

## 6. google/shieldgemma-2b
Source: https://ai.google.dev/gemma/docs/shieldgemma/model_card (Last updated 2025-02-25 UTC); HF repo gated; API created 2024-07-16, license gemma.
- Licence: HF API "license: gemma"; card: "As with other models that are part of the Gemma ecosystem, ShieldGemma is subject to Google's prohibited use policies."
- Params: "available in English with open weights, including models of 3 sizes: 2B, 9B and 27B parameters" (API 2,614,341,888 for 2b).
- Languages: "available in English"
- Context length: NOT FOUND (gated config).
- Detects: "target four harm categories (sexually explicit, dangerous content, hate, and harassment)". No prompt injection/jailbreak/PII category. Output "start with the token 'Yes' or 'No'".
- Metrics (Optimal F1 / AU-PRC): ShieldGemma 2B: SG Prompt 0.825/0.887; OpenAI Mod 0.812/0.887; ToxicChat 0.704/0.778; SG Response 0.743/0.802. Latency NOT FOUND.
- Caveat: "ShieldGemma is also highly sensitive to the specific user-provided description of safety principles, and might perform unpredictably".

## 7. qualifire/prompt-injection-sentinel
Source: https://huggingface.co/qualifire/prompt-injection-sentinel (via exa; HF API lastModified 2025-09-22, created 2025-05-28; paper arXiv:2506.05446)
- Licence: card page text shows none; HF API "license: other" (UNVERIFIED actual terms; likely gated with custom terms, check repo before commercial use).
- Params: "Model size 0.4B params" (API 395,833,346); "fine-tuned version of a ModernBERT-large architecture".
- Languages: API "en"; "Not evaluated on non-English data".
- Context: NOT FOUND in card (ModernBERT-large is not stated).
- Detects: "trained to detect prompt injection attacks in LLM inputs. It classifies whether a given prompt is benign or malicious (jailbreak attempt)." Example output label 'jailbreak'. Indirect injection / PII / harm: NOT FOUND.
- Metrics: "Metric: Binary F1 Score": sentinel Avg 93.86 (wildjailbreak 93.57; jackhhao 98.56; deepset 85.71; qualifire benchmark 97.62) vs protectai/deberta-v3-base-prompt-injection-v2 Avg 70.93 (73.32; 91.53; 53.65; 65.22). Vendor self-reported on own benchmark. AUC/precision/recall/FPR/latency NOT FOUND.
- Limits: "May misclassify creative or ambiguous prompts"; "Not for use in high-risk environments without human oversight".
