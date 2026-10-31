---
name: register
description: Add a project (or a repo to an existing project) to the brain registry and create its brain folder from the template. Trigger /base:register [project] [repo-name=path ...].
argument-hint: "[project] [repo=path ...]"
---

# /base:register

The registry is `<brain_dir>/registry.json`. Each project has `kind`, `status`, `summary` and
`repos` (a map of repo name to local path; `~` is allowed).

## Steps

1. **Collect.** From the arguments, or by asking Keshav one short question per missing item:
   project name (kebab-case), kind (`product`, `service`, `library`, `research`, `infra`),
   one-line summary, and each repo as `name=path`. If the current directory is a git repo that is
   not registered, offer it as a repo.
2. **Check.** For each path: does it exist, and is it a git repo (`git -C <path> rev-parse`)?
   Report problems; register a missing path only if Keshav confirms.
3. **Write the registry.** Read `registry.json`, add or merge the project, keep every other
   entry unchanged, write it back with 2-space indentation. Never drop a repo without asking.
4. **Create the brain folder** for a new project: copy every file in
   `${CLAUDE_PLUGIN_ROOT}/templates/project/` to `<brain_dir>/projects/<project>/`, and replace
   `{{project}}` in each file with the project name. Do not overwrite existing files.
5. **Confirm** with the `mcp__base__where` tool for the project, and show the card.
