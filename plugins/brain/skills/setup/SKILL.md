---
name: setup
description: One-time and repeatable setup for the harness — writes the user settings that plugins cannot ship (attribution off, lazy MCP connect), checks context_dir and the registry, and checks MCP prerequisites. Trigger /brain:setup.
---

# /brain:setup

Plugins cannot set `attribution`, `env`, `permissions` or `statusLine`. This skill writes the
ones the harness needs into `~/.claude/settings.json`. It is idempotent: run it again at any time.

## Steps

1. **Read** `~/.claude/settings.json` (it may not exist). Never drop keys you did not add.
2. **Build the target** by merging these keys into it:
   ```json
   {
     "attribution": { "commit": "", "pr": "" },
     "env": { "MCP_DISCOVERY_CACHE": "1" }
   }
   ```
   `MCP_DISCOVERY_CACHE=1` makes a remote MCP server you used before connect on first use
   instead of at startup. Tool search (deferred MCP tools) is already the default; do not set
   `ENABLE_TOOL_SEARCH`.
3. **Show Keshav the diff** (old vs new JSON for the changed keys only). Write only after he says yes.
4. **context_dir.** Check that the brain plugin option `context_dir` is set (`/config` shows it under
   the plugin). It must point to the `context/` folder of the harness repo. If unset, tell Keshav
   to set it in `/config`; do not edit `pluginConfigs` by hand.
5. **Registry.** Check `<context_dir>/registry.json` parses as JSON with a `projects` object.
   For each repo path, report whether it exists on disk.
6. **Prerequisites.** Run and report each one as OK or MISSING, with the fix:
   - `gh auth status` — the GitHub MCP server uses `gh auth token`. Fix: `gh auth login`.
   - `npx --version` — Context7, Reddit and Playwright run with npx. Fix: install Node.
   - `uvx --version` — the arXiv MCP server runs with uvx. Fix: `brew install uv`.
7. **Report** one line per step: OK, CHANGED, or MISSING + fix. Remind Keshav to restart Claude
   Code after a settings change.
