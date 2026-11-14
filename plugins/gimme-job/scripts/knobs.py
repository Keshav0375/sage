#!/usr/bin/env python3
"""Knobs: merge defaults → preset → user overrides → CLI flags, validate, show provenance.

Usage:
  knobs.py show [--preset NAME] [--json]
  knobs.py brief [--preset NAME]            # 5-line summary (SessionStart hook)
  knobs.py get KEY.PATH [--preset NAME]
  knobs.py set KEY.PATH VALUE               # writes memory/resume/knobs.toml
  knobs.py presets
  knobs.py validate [--preset NAME]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tomllib
from pathlib import Path
from typing import Any

PLUGIN = Path(__file__).resolve().parent.parent
CONFIG = PLUGIN / "config"
DEFAULTS = CONFIG / "knobs.default.toml"
SCHEMA = CONFIG / "knobs.schema.json"
PRESETS = CONFIG / "presets"


def repo_root() -> Path:
    env = os.environ.get("GIMME_JOB_REPO")
    if env:
        return Path(env)
    p = PLUGIN
    for parent in [p, *p.parents]:
        if (parent / ".git").exists():
            return parent
    return Path.cwd()


def user_file() -> Path:
    return Path(os.environ.get("GIMME_JOB_KNOBS", repo_root() / "memory" / "resume" / "knobs.toml"))


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f)


def _merge(base: dict, over: dict, src: str, prov: dict, prefix: str = "") -> dict:
    out = dict(base)
    for k, v in over.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v, src, prov, key + ".")
        else:
            out[k] = v
            _mark(v, key, src, prov)
    return out


def _mark(v: Any, key: str, src: str, prov: dict) -> None:
    if isinstance(v, dict):
        for k2, v2 in v.items():
            _mark(v2, f"{key}.{k2}", src, prov)
    else:
        prov[key] = src


def _parse_value(raw: str) -> Any:
    try:
        return tomllib.loads(f"v = {raw}")["v"]
    except tomllib.TOMLDecodeError:
        return raw


def load(preset: str | None = None, flags: dict[str, Any] | None = None) -> tuple[dict, dict]:
    """Return (knobs, provenance{dotted_key: source})."""
    prov: dict[str, str] = {}
    base = _load(DEFAULTS)
    _mark(base, "", "default", prov)
    prov = {k.lstrip("."): v for k, v in prov.items()}
    knobs = base
    if preset:
        p = PRESETS / f"{preset}.toml"
        if not p.exists():
            raise SystemExit(f"unknown preset {preset!r}; have: {', '.join(list_presets())}")
        knobs = _merge(knobs, _load(p), f"preset:{preset}", prov)
    knobs = _merge(knobs, _load(user_file()), "user", prov)
    for dotted, val in (flags or {}).items():
        set_path(knobs, dotted, val)
        prov[dotted] = "flag"
    errors = validate(knobs)
    if errors:
        raise SystemExit("invalid knobs:\n  " + "\n  ".join(errors))
    return knobs, prov


def set_path(d: dict, dotted: str, value: Any) -> None:
    parts = dotted.split(".")
    cur = d
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value


def get_path(d: dict, dotted: str) -> Any:
    cur: Any = d
    for p in dotted.split("."):
        if not isinstance(cur, dict) or p not in cur:
            raise KeyError(dotted)
        cur = cur[p]
    return cur


def list_presets() -> list[str]:
    return sorted(p.stem for p in PRESETS.glob("*.toml"))


# ------------------------------------------------------------------ validation
_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}


def validate(knobs: dict) -> list[str]:
    if not SCHEMA.exists():
        return []
    schema = json.loads(SCHEMA.read_text())
    errs: list[str] = []
    _check(knobs, schema, "", errs)
    return errs


def _check(val: Any, sch: dict, path: str, errs: list[str]) -> None:
    t = sch.get("type")
    if t:
        py = _TYPES[t]
        if t == "integer" and isinstance(val, bool) or (t == "number" and isinstance(val, bool)):
            errs.append(f"{path or '<root>'}: expected {t}, got bool")
            return
        if not isinstance(val, py):
            errs.append(f"{path or '<root>'}: expected {t}, got {type(val).__name__} ({val!r})")
            return
    if "enum" in sch and val not in sch["enum"]:
        errs.append(f"{path}: {val!r} not in {sch['enum']}")
    if "minimum" in sch and isinstance(val, (int, float)) and val < sch["minimum"]:
        errs.append(f"{path}: {val} < minimum {sch['minimum']}")
    if "maximum" in sch and isinstance(val, (int, float)) and val > sch["maximum"]:
        errs.append(f"{path}: {val} > maximum {sch['maximum']}")
    if isinstance(val, list) and "items" in sch:
        for i, item in enumerate(val):
            _check(item, sch["items"], f"{path}[{i}]", errs)
    if isinstance(val, dict):
        props = sch.get("properties", {})
        for k, v in val.items():
            if k in props:
                _check(v, props[k], f"{path}.{k}" if path else k, errs)
            elif "additionalProperties" in sch and isinstance(sch["additionalProperties"], dict):
                _check(v, sch["additionalProperties"], f"{path}.{k}" if path else k, errs)
            elif sch.get("additionalProperties") is False:
                errs.append(f"{path}.{k}: unknown knob" if path else f"{k}: unknown knob")


# ------------------------------------------------------------------ TOML writer (for `set`)
def _toml_value(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, list):
        return "[" + ", ".join(_toml_value(x) for x in v) + "]"
    return json.dumps(str(v))


def dump_toml(d: dict) -> str:
    lines: list[str] = []

    def walk(node: dict, prefix: str) -> None:
        scalars = {k: v for k, v in node.items() if not isinstance(v, dict)}
        tables = {k: v for k, v in node.items() if isinstance(v, dict)}
        if scalars and prefix:
            lines.append(f"[{prefix}]")
        for k, v in scalars.items():
            lines.append(f"{k} = {_toml_value(v)}")
        if scalars:
            lines.append("")
        for k, v in tables.items():
            walk(v, f"{prefix}.{k}" if prefix else k)

    walk(d, "")
    return "\n".join(lines).rstrip() + "\n"


def cmd_set(dotted: str, raw: str) -> None:
    uf = user_file()
    cur = _load(uf)
    set_path(cur, dotted, _parse_value(raw))
    merged = _merge(_load(DEFAULTS), cur, "user", {})
    errs = validate(merged)
    if errs:
        raise SystemExit("not saved, invalid:\n  " + "\n  ".join(errs))
    uf.parent.mkdir(parents=True, exist_ok=True)
    uf.write_text("# gimme-job user knobs (overrides). Edit or use `knobs.py set`.\n" + dump_toml(cur))
    print(f"set {dotted} = {_toml_value(_parse_value(raw))} in {uf}")


def flatten(d: dict, prefix: str = "") -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            out.update(flatten(v, key))
        else:
            out[key] = v
    return out


def brief(k: dict) -> str:
    s = k["search"]
    waves = k["sources"]["ats_scanners"]["waves"] if k["sources"]["ats_scanners"]["enabled"] else []
    apis = [n for n, v in k["sources"].items() if n != "ats_scanners" and v.get("enabled")]
    return "\n".join([
        f"gimme-job knobs: titles={len(k['profile']['target_titles'])} years={k['profile']['years_experience']} min_base={k['profile']['min_base']} {k['profile']['currency']}",
        f"  where: {', '.join(s['locations'])} | workplace={','.join(s['workplace'])} | posted<={s['date_posted']}",
        f"  sources: waves={','.join(waves) or 'off'} + {', '.join(apis)}",
        f"  ranking: top_k={k['ranking']['pre_rank_top_k']} select={k['ranking']['select_top_n']} min={k['ranking']['select_min']} | loop pass={k['loop']['pass_score']} max_iter={k['loop']['max_iterations']}",
        f"  budget: ${k['budget']['max_usd_per_run']}/run, {k['budget']['max_composio_calls']} API calls, concurrency {k['budget']['concurrency']}",
    ])


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["show", "brief", "get", "set", "presets", "validate"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--preset")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "presets":
        print("\n".join(list_presets()))
        return 0
    if a.cmd == "set":
        if len(a.args) != 2:
            ap.error("set KEY.PATH VALUE")
        cmd_set(a.args[0], a.args[1])
        return 0
    k, prov = load(a.preset)
    if a.cmd == "validate":
        print("ok")
    elif a.cmd == "brief":
        print(brief(k))
    elif a.cmd == "get":
        print(json.dumps(get_path(k, a.args[0])))
    elif a.json:
        print(json.dumps(k, indent=2))
    else:
        flat = flatten(k)
        width = max(len(x) for x in flat)
        for key, v in flat.items():
            print(f"{key:<{width}}  {json.dumps(v)}  [{prov.get(key, 'default')}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
