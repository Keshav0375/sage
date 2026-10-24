---
name: forge-agent
description: Create a new specialist agent (or retire unused ones) when a recurring job has no good owner — agent-smith drafts it into incubator/agents/ with a typed handoff and evals; it graduates into .claude/agents/ only after its evals pass and Keshav approves. Also covers one-off throwaway agents via `claude --agents`. Trigger /forge-agent <need>.
argument-hint: "<the recurring job that needs an owner>"
disable-model-invocation: true
---

# /forge-agent

1. Evidence first: how often has this job come up (`sagectl mine`, traces, lessons)? Once is
   not a pattern. For a one-off, define a **throwaway agent** instead:
   `claude --agents '{"<name>": {"description": "…", "prompt": "…", "tools": ["Read","Grep"], "model": "sonnet"}}'`
   for that session only. Nothing is committed.
2. Recurring → `agent-smith` with NEED + evidence. It may answer "extend agent X instead". Respect that.
3. Run the new agent's evals (`sagectl eval run -p … --split heldin`) with it temporarily copied
   into `.claude/agents/`.
4. Keshav approves → `git mv incubator/agents/<name>.md .claude/agents/`, then `sagectl audit` to
   confirm the context budget still holds. Retirements from the RETIRE line go through `sagectl trash put`.
