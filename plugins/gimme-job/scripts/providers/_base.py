"""Provider contract for gimme-job scanners.

Every scanner is one module in this folder (names starting with "_" are helpers, not scanners).
A scanner module defines a module-level ``PROVIDER`` instance of a ``Provider`` subclass.

Mechanism adapted from career-ops (MIT, v1.40.0) providers/_types.js; code is our own.

Rules for every scanner:
- Standard library only. All network access goes through ``ctx.http`` (never urllib directly),
  so robots.txt, crawl delay, retries, body caps and test transports apply.
- Public, no-auth endpoints only. No login, no cookies from a browser session, no CAPTCHA bypass.
- Never invent fields. Leave a field empty when the source does not give it.
- ``fetch`` returns a list of ``Job``; it raises ``ProviderError`` on a hard failure.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

WORKPLACES = ("remote", "hybrid", "onsite")


class ProviderError(Exception):
    """Hard failure for one target (bad slug, endpoint gone, parse error)."""


@dataclass
class Job:
    title: str
    url: str
    source: str
    company: str = ""
    location: str = ""
    locations: list[str] = field(default_factory=list)
    country: str = ""
    workplace: str = ""          # remote | hybrid | onsite | "" (only when the source says so)
    employment: str = ""         # fulltime | contract | parttime | intern | temporary | ""
    posted_at: str = ""          # ISO 8601 date or datetime, as given by the source
    closes_at: str = ""
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = ""
    salary_period: str = ""      # year | month | hour | ""
    description: str = ""        # only when the list payload carries it for free
    department: str = ""
    source_id: str = ""          # the source's own job id when given
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        key = f"{self.source}:{self.source_id}" if self.source_id else self.url
        return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]

    def validate(self) -> "Job":
        self.title = (self.title or "").strip()
        self.url = (self.url or "").strip()
        if not self.title:
            raise ProviderError("job without title")
        if not self.url.startswith(("http://", "https://")):
            raise ProviderError(f"job url not absolute: {self.url!r}")
        if self.workplace and self.workplace not in WORKPLACES:
            self.workplace = ""
        if not self.location and self.locations:
            self.location = " | ".join(self.locations)
        return self

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["id"] = self.id
        return d


@dataclass
class Target:
    """What to scan. Board-wide providers get a Target with only ``query``/``options``."""
    company: str = ""
    slug: str = ""
    careers_url: str = ""
    api_url: str = ""
    query: str = ""
    location: str = ""
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class Context:
    http: Any                      # scripts.providers._http.Http
    knobs: dict[str, Any] = field(default_factory=dict)
    max_jobs: int = 500
    log: Any = None

    def warn(self, msg: str) -> None:
        if self.log:
            self.log(msg)


class Provider:
    name: str = ""
    wave: str = ""                 # W1..W6
    kind: str = ""                 # ats | board | company | feed | public
    tenant: bool = True            # True: needs a company Target (slug/careers_url); False: board-wide
    hosts: tuple[str, ...] = ()    # hostnames this provider talks to (used by detect + allowlist)

    def detect(self, careers_url: str) -> Optional[Target]:
        """Return a Target when ``careers_url`` belongs to this provider, else None."""
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        raise NotImplementedError

    # helper so subclasses build jobs with source filled in
    def job(self, **kw: Any) -> Job:
        kw.setdefault("source", self.name)
        return Job(**kw)
