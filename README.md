# Harness

Keshav's Claude Code harness: one marketplace of plugins, plus the context folder that holds every
project's registry entry, architecture, decisions and lessons.

```
.claude-plugin/marketplace.json   marketplace "hq"
plugins/brain/     registry + context mod, guards, attribution, model routing, lazy MCP, STE style
plugins/researcher/  research + architecture agent: docs, reference systems, papers, arch with diagrams, GitHub epics and tickets
plugins/builder/     builder agent: epic loop with fetcher, brancher, editor, code-reviewer, runner, warden, verifier
plugins/observe/  JSONL traces of tools, subagents, turns
plugins/ui/       terminal UI mod (scaffold only)
context/            data: registry.json, routing.json, projects/<p>/, library/
```

## Install

Inside this repo, `.claude/settings.json` registers the marketplace and enables the plugins.
For every other repo, run once:

```
/plugin marketplace add ~/Projects/sage
/plugin install brain@hq researcher@hq builder@hq observe@hq
```

Then set the `brain` plugin option `context_dir` to `~/Projects/sage/context` in `/config`, and run
`/brain:setup`.

## Develop

```
claude plugin validate ./plugins/<name>
cd plugins/brain && claude plugin test
```

Tested with Claude Code 2.1.314.
