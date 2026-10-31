---
name: council
description: LLM council for a hard judgment call — several councilors answer independently through different lenses and models, rank each other's anonymized answers, then the main session gives the verdict with the strongest dissent. Trigger /think:council <question>.
argument-hint: "<question>"
---

# /think:council

1. **Lenses.** Pick 3-5 lenses that fit the question (for example: first principles, operator on
   call, cost owner, security, the user, contrarian).
2. **Answer (one message, in parallel).** Spawn one `think:councilor` per lens with
   `mode=answer`. Spread models: pass `model: opus` to some and `model: sonnet` to others.
3. **Anonymize.** Label the answers A, B, C... in random order. Remove lens and model names.
4. **Rank (one message, in parallel).** Spawn the same number of `think:councilor` with
   `mode=rank`, each given all anonymized answers.
5. **Verdict (main session).** Combine the rankings and your own reading. Give the verdict, the
   reasoning, and the strongest dissent in its best form. Say how confident you are.
6. **Save** to `brain/library/council/<yyyy-mm-dd>-<slug>.md`: question, answers, rankings,
   verdict, dissent.
