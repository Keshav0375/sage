# Harness

Keshav's Claude Code harness: one marketplace of plugins, plus the brain that holds every
project's registry entry, architecture, decisions and lessons.

```
.claude-plugin/marketplace.json   marketplace "hq"
plugins/base/     registry + context mod, guards, attribution, model routing, lazy MCP, STE style
plugins/researcher/  research + architecture agent: docs, reference systems, papers, arch with diagrams, GitHub epics and tickets
plugins/builder/     builder agent: epic loop with fetcher, brancher, editor, code-reviewer, runner, warden, verifier
plugins/observe/  JSONL traces of tools, subagents, turns
plugins/ui/       terminal UI mod (scaffold only)
brain/            data: registry.json, routing.json, projects/<p>/, library/
```

## Install

Inside this repo, `.claude/settings.json` registers the marketplace and enables the plugins.
For every other repo, run once:

```
/plugin marketplace add ~/Projects/sage
/plugin install base@hq researcher@hq builder@hq observe@hq
```

Then set the `base` option `brain_dir` to `~/Projects/sage/brain` in `/config`, and run
`/base:setup`.

## Develop

```
claude plugin validate ./plugins/<name>
cd plugins/base && claude plugin test
```

Tested with Claude Code 2.1.314.
