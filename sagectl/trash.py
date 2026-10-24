"""Local trash. The guard rewrites a plain `rm` into `sagectl trash put`, so deletes are moves:
.sage/trash/<stamp>/ holds the files plus a manifest to restore them. Purge is explicit and
age-gated (default 14 days)."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

from . import paths


def put(targets: list[str], cwd: str | None = None) -> int:
    base = Path(cwd) if cwd else Path.cwd()
    stamp = time.strftime("%Y%m%d-%H%M%S") + f"-{int(time.time() * 1000) % 1000:03d}"
    bucket = paths.ensure(paths.TRASH / stamp)
    moved = []
    for t in targets:
        src = (base / t).resolve() if not Path(t).is_absolute() else Path(t)
        if not src.exists() and not src.is_symlink():
            print(f"trash: skip (missing) {t}")
            continue
        dest = bucket / str(src).lstrip("/").replace("/", "__")
        shutil.move(str(src), dest)
        moved.append({"from": str(src), "stored": dest.name})
        print(f"trash: {src} → .sage/trash/{stamp}/")
    if moved:
        (bucket / "manifest.json").write_text(json.dumps(moved, indent=1))
    else:
        bucket.rmdir()
    return 0


def entries() -> list[tuple[str, list[dict]]]:
    if not paths.TRASH.is_dir():
        return []
    out = []
    for b in sorted(paths.TRASH.iterdir()):
        man = b / "manifest.json"
        if man.is_file():
            out.append((b.name, json.loads(man.read_text())))
    return out


def list_() -> int:
    rows = entries()
    if not rows:
        print("trash is empty")
    for stamp, items in rows:
        for it in items:
            print(f"{stamp}  {it['from']}")
    return 0


def restore(stamp: str) -> int:
    bucket = paths.TRASH / stamp
    man = bucket / "manifest.json"
    if not man.is_file():
        raise SystemExit(f"no trash entry {stamp}")
    for it in json.loads(man.read_text()):
        dest = Path(it["from"])
        if dest.exists():
            print(f"restore: {dest} exists — left in trash")
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(bucket / it["stored"]), dest)
        print(f"restored {dest}")
    if not [p for p in bucket.iterdir() if p.name != "manifest.json"]:
        shutil.rmtree(bucket)
    return 0


def purge(days: int = 14) -> int:
    cutoff = time.time() - days * 86400
    n = 0
    for b in paths.TRASH.iterdir() if paths.TRASH.is_dir() else []:
        if b.stat().st_mtime < cutoff:
            shutil.rmtree(b)
            n += 1
    print(f"purged {n} trash bucket(s) older than {days}d")
    return 0
