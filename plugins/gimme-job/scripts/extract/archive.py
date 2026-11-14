"""Keep JD text by content hash, even after the post is taken down."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .fingerprint import text_hash


def save(text: str, root) -> str:
    h = text_hash(text)
    p = Path(root)
    p.mkdir(parents=True, exist_ok=True)
    f = p / f"{h}.txt"
    if not f.exists():
        f.write_text(text, encoding="utf-8")
    return h


def load(hash: str, root) -> Optional[str]:
    f = Path(root) / f"{hash}.txt"
    return f.read_text(encoding="utf-8") if f.exists() else None
