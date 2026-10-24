"""Weakness mining (after Self-Harness, arXiv 2606.09498): turn scattered failures into a short
list of recurring failure *mechanisms*, biggest first.

This is the deterministic pre-pass. It normalises every failure signal — lessons, tool failures,
user corrections — into a token signature, then greedily clusters by Jaccard similarity. The
`miner` agent then names each cluster's mechanism and picks representatives; the
`harness-smith` proposes one minimal edit per mechanism.
"""

from __future__ import annotations

import json
import re

from . import project as projects
from . import trace

STOP = set("""a an the to of in on for and or is was be it this that with as at by from not no
you your i me my we our should would could did does do done have has had then than but if so
into out up its it's are were been""".split())
NOISE = re.compile(r"(/[\w.\-/]+|0x[0-9a-f]+|\b\d+(?:\.\d+)*\b|[\"'`].*?[\"'`])", re.I)


def signature(text: str) -> frozenset[str]:
    text = NOISE.sub(" ", text.lower())
    return frozenset(w for w in re.findall(r"[a-z][a-z_\-]{2,}", text) if w not in STOP)


def signals(project: str | None, days: int) -> list[dict]:
    out = []
    names = [project] if project else projects.names()
    for p in names:
        for l in trace.load_lessons(p):
            if l.get("status") == "fixed":
                continue
            text = " ".join([l["what"], l["root_cause"], " ".join(l.get("tags", []))])
            out.append({"kind": "lesson", "project": p, "ref": l["id"], "text": text})
    for r in trace.read(days=days, project=project):
        if r["event"] == "tool_failure":
            out.append({"kind": "tool_failure", "project": r.get("project"), "ref": r["ts"],
                        "text": f"{r.get('tool')} {r.get('error', '')}"})
        elif r["event"] == "correction":
            out.append({"kind": "correction", "project": r.get("project"), "ref": r["ts"],
                        "text": r.get("prompt", "")})
    for s in out:
        s["sig"] = signature(s["text"])
    return [s for s in out if s["sig"]]


def jaccard(a: frozenset, b: frozenset) -> float:
    return len(a & b) / len(a | b) if a | b else 0.0


def cluster(items: list[dict], threshold: float = 0.3) -> list[dict]:
    clusters: list[dict] = []
    for it in items:
        best, score = None, 0.0
        for c in clusters:
            s = jaccard(it["sig"], c["centroid"])
            if s > score:
                best, score = c, s
        if best is not None and score >= threshold:
            best["members"].append(it)
            # centroid = tokens shared by at least half the members
            counts: dict[str, int] = {}
            for m in best["members"]:
                for w in m["sig"]:
                    counts[w] = counts.get(w, 0) + 1
            half = len(best["members"]) / 2
            best["centroid"] = frozenset(w for w, n in counts.items() if n >= half) or it["sig"]
        else:
            clusters.append({"centroid": it["sig"], "members": [it]})
    clusters.sort(key=lambda c: -len(c["members"]))
    return clusters


def report(project: str | None, days: int = 30, as_json: bool = False, min_size: int = 1) -> str:
    cl = [c for c in cluster(signals(project, days)) if len(c["members"]) >= min_size]
    if as_json:
        return json.dumps([{
            "id": f"C{i + 1}", "size": len(c["members"]),
            "keywords": sorted(c["centroid"])[:12],
            "kinds": sorted({m["kind"] for m in c["members"]}),
            "projects": sorted({m["project"] or "-" for m in c["members"]}),
            "examples": [{"kind": m["kind"], "ref": m["ref"], "text": m["text"][:240]} for m in c["members"][:5]],
        } for i, c in enumerate(cl)], indent=1)
    if not cl:
        return "no failure signals yet — log lessons (/retro) and let the trace hooks run."
    lines = [f"{len(cl)} cluster(s) from {sum(len(c['members']) for c in cl)} signal(s), last {days}d"]
    for i, c in enumerate(cl):
        kinds = ",".join(sorted({m["kind"] for m in c["members"]}))
        lines.append(f"C{i + 1}  ×{len(c['members']):<3} [{kinds}]  {' '.join(sorted(c['centroid'])[:8])}")
        for m in c["members"][:3]:
            lines.append(f"      · {m['project'] or '-'} {m['ref']}: {m['text'][:110]}")
    return "\n".join(lines)
