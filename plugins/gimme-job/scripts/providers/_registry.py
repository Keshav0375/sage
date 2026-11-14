"""Discover scanner modules: every ``providers/<name>.py`` (not starting with "_") with a ``PROVIDER``."""
from __future__ import annotations

import importlib
import pkgutil
from typing import Optional

from ._base import Provider, Target

_CACHE: Optional[dict[str, Provider]] = None


def all_providers() -> dict[str, Provider]:
    global _CACHE
    if _CACHE is None:
        from . import __path__ as pkg_path  # type: ignore
        found: dict[str, Provider] = {}
        for mod in pkgutil.iter_modules(pkg_path):
            if mod.name.startswith("_"):
                continue
            m = importlib.import_module(f"{__package__}.{mod.name}")
            p = getattr(m, "PROVIDER", None)
            if isinstance(p, Provider):
                if not p.name:
                    raise RuntimeError(f"provider in {mod.name} has no name")
                found[p.name] = p
        _CACHE = dict(sorted(found.items()))
    return _CACHE


def get(name: str) -> Provider:
    try:
        return all_providers()[name]
    except KeyError:
        raise KeyError(f"unknown provider {name!r}") from None


def by_wave(waves: list[str]) -> list[Provider]:
    return [p for p in all_providers().values() if p.wave in waves]


def detect(careers_url: str) -> Optional[tuple[Provider, Target]]:
    """First provider whose detect() claims this careers URL."""
    for p in all_providers().values():
        try:
            t = p.detect(careers_url)
        except Exception:
            t = None
        if t:
            return p, t
    return None
