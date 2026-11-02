"""Token usage per session, per subagent type, per model and per spawn depth, from Claude Code
transcripts.

Layout (Claude Code): <projects>/<project>/<session>.jsonl is the main loop;
<projects>/<project>/<session>/subagents/agent-<id>.jsonl is one subagent, with agent-<id>.meta.json
holding agentType, spawnDepth and model. Each API response can span several transcript lines that
repeat the same usage, so usage is counted once per message id.

Usage: python3 usage.py [--days N] [--session ID] [--projects DIR] [--out DIR]
Writes usage-<date>.json and usage-<date>.md to --out (default: the observe trace dir) and prints
the markdown.
"""

import argparse
import datetime
import glob
import json
import os
import sys

FIELDS = ("input", "cache_write", "cache_read", "output")


def empty() -> dict:
    return {k: 0 for k in FIELDS} | {"calls": 0}


def add(total: dict, part: dict) -> None:
    for k in FIELDS + ("calls",):
        total[k] += part.get(k, 0)


def transcript_usage(path: str) -> dict:
    """Usage of one transcript file, by model: {model: {input, cache_write, cache_read, output, calls}}."""
    seen = set()
    by_model: dict = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if '"usage"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                msg = d.get("message") or {}
                usage = msg.get("usage")
                if d.get("type") != "assistant" or not isinstance(usage, dict):
                    continue
                key = msg.get("id") or d.get("uuid")
                if key in seen:
                    continue
                seen.add(key)
                m = by_model.setdefault(msg.get("model") or "unknown", empty())
                m["input"] += usage.get("input_tokens") or 0
                m["cache_write"] += usage.get("cache_creation_input_tokens") or 0
                m["cache_read"] += usage.get("cache_read_input_tokens") or 0
                m["output"] += usage.get("output_tokens") or 0
                m["calls"] += 1
    except OSError:
        pass
    return by_model


def subagent_record(path: str) -> dict:
    """One subagent: type, depth, model asked for, and its usage by model."""
    meta = {}
    try:
        with open(path[: -len(".jsonl")] + ".meta.json", encoding="utf-8") as f:
            meta = json.load(f)
    except (OSError, ValueError):
        pass
    agent_id = os.path.basename(path)[len("agent-") : -len(".jsonl")]
    return {
        "agent_id": agent_id,
        "agent_type": meta.get("agentType", "unknown"),
        "description": meta.get("description", ""),
        "depth": meta.get("spawnDepth", 1),
        "requested_model": meta.get("model"),
        "finished": meta.get("finished"),
        "usage": transcript_usage(path),
    }


def collect(projects: str, days: int, session: str | None) -> list:
    """Sessions modified within `days` (or the one named), each with main and subagent usage."""
    cutoff = datetime.datetime.now().timestamp() - days * 86400
    out = []
    for main in glob.glob(os.path.join(projects, "*", "*.jsonl")):
        sid = os.path.basename(main)[: -len(".jsonl")]
        if session and sid != session:
            continue
        if not session and os.path.getmtime(main) < cutoff:
            continue
        subdir = os.path.join(os.path.dirname(main), sid, "subagents")
        subs = [subagent_record(p) for p in sorted(glob.glob(os.path.join(subdir, "agent-*.jsonl")))]
        out.append({
            "session": sid,
            "project": os.path.basename(os.path.dirname(main)),
            "main": transcript_usage(main),
            "subagents": subs,
        })
    return out


def total_of(by_model: dict) -> dict:
    t = empty()
    for part in by_model.values():
        add(t, part)
    return t


def summarize(sessions: list) -> dict:
    by_type: dict = {}
    by_model: dict = {}
    by_depth: dict = {}
    main_total = empty()
    for s in sessions:
        for model, part in s["main"].items():
            add(main_total, part)
            add(by_model.setdefault(model, empty()), part)
        for a in s["subagents"]:
            t = total_of(a["usage"])
            row = by_type.setdefault(a["agent_type"], empty() | {"agents": 0})
            add(row, t)
            row["agents"] += 1
            add(by_depth.setdefault(str(a["depth"]), empty()), t)
            for model, part in a["usage"].items():
                add(by_model.setdefault(model, empty()), part)
    return {"main": main_total, "by_type": by_type, "by_model": by_model, "by_depth": by_depth}


def fmt(n: int) -> str:
    return f"{n / 1e6:.2f}M" if n >= 1e6 else f"{n / 1e3:.0f}k"


def table(title: str, rows: dict, extra: str | None = None) -> list:
    head = f"| {title} |" + (f" {extra} |" if extra else "") + " calls | input | cache write | cache read | output |"
    lines = [head, "|" + "---|" * (head.count("|") - 1)]
    order = sorted(rows.items(), key=lambda kv: -(kv[1]["cache_write"] + kv[1]["cache_read"] + kv[1]["input"]))
    for name, r in order:
        cells = [name] + ([str(r.get(extra, ""))] if extra else [])
        cells += [str(r["calls"])] + [fmt(r[k]) for k in FIELDS]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def markdown(summary: dict, sessions: list) -> str:
    lines = [f"# Token usage ({len(sessions)} sessions)", ""]
    lines += table("main loop", {"main": summary["main"]}) + [""]
    lines += table("model", summary["by_model"]) + [""]
    lines += table("subagent type", summary["by_type"], "agents") + [""]
    lines += table("spawn depth", summary["by_depth"]) + [""]
    lines.append("Cache read is billed at a fraction of input; cache write above input. Compare models by the")
    lines.append("same columns, not by one total.")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--session")
    ap.add_argument("--projects", default=os.path.expanduser("~/.claude/projects"))
    ap.add_argument("--out", default=os.environ.get("CLAUDE_PLUGIN_OPTION_TRACE_DIR", ""))
    args = ap.parse_args()
    sessions = collect(args.projects, args.days, args.session)
    summary = summarize(sessions)
    text = markdown(summary, sessions)
    if args.out:
        out = os.path.expanduser(args.out)
        os.makedirs(out, exist_ok=True)
        stamp = datetime.date.today().isoformat()
        with open(os.path.join(out, f"usage-{stamp}.json"), "w", encoding="utf-8") as f:
            json.dump({"summary": summary, "sessions": sessions}, f, indent=1)
        with open(os.path.join(out, f"usage-{stamp}.md"), "w", encoding="utf-8") as f:
            f.write(text + "\n")
    sys.stdout.write(text + "\n")


if __name__ == "__main__":
    main()
