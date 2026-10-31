---
name: check
description: Run the active project's quality gate through an independent verifier and report the verdict, tree state and attribution check. Use when asked to check, lint, test or verify.
---

# /build:check

1. Get the project with `mcp__base__where`, and read its `gate` from `brain/registry.json`:
   a map of repo name to a list of commands, for example
   `"gate": { "api": ["npm run lint", "npm test"] }`.
2. If the project has no `gate`, ask Keshav for the commands and offer to add them.
3. Spawn `build:verifier` with the repo paths and the commands.
4. Report its verdict as is. Only `GREEN` is green.
