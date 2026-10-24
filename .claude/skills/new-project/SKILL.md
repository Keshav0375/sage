---
name: new-project
description: Onboard a new project into sage — scaffold projects/<name>/ with a stack-detected project.toml (gate, formatter, LSP), install the matching LSP plugins, wire research sources, and set it active. Trigger /new-project <name> [repo paths].
argument-hint: "<name> [name=path ...] [--kind code|research|qa]"
disable-model-invocation: true
---

# /new-project

1. **Ask only what you can't detect** (one message): what the project is (one line), kind
   (`code` / `research` / `qa`), repo paths (relative to sage, e.g. `app=../my-app`), anything
   agents must never read (dead zones), subreddits and libraries worth watching.
2. `python3 bin/sagectl new <name> --repo <n=path> … --kind <kind> --description "<line>"`.
   It detects each repo's stack and proposes the gate, formatter and LSP servers.
3. Show Keshav the generated `projects/<name>/project.toml` and **verify the gate commands
   actually exist** in the repo (e.g. `npm run lint` needs a `lint` script). Fix what's wrong
   with him. Don't guess.
4. **LSP:** for each `[lsp] servers` entry, print the `/plugin install …` lines `sagectl new`
   suggested and ask Keshav to run them (plugin installs are his to approve). Plugin names
   drift, so confirm with `/plugin` search. The language server binary itself must be on PATH
   (`pyright`, `typescript-language-server`, `gopls`…). Say which are missing.
5. `python3 bin/sagectl use <name>`, then `python3 bin/sagectl gate -p <name>` once to prove the
   gate runs (RED is fine on day one; INCONCLUSIVE is not).
6. Fill `[research]` (subreddits, docs) from his answer.
7. Next: `/spec` to write the architecture (code projects), or `/research` / `/grill`
   (research / qa projects).

Never create files inside the project's code repos. sage files stay in sage.
