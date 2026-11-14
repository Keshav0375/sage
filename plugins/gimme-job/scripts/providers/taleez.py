"""Taleez — https://<tenant>.taleez.com/api/careez (site object with jobs[]).

Mechanism from career-ops providers/taleez.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

HOST = re.compile(r"^([a-z0-9][a-z0-9-]*)\.taleez\.com$")
RESERVED = {"www", "app", "api", "blog", "files", "static", "help", "aide", "status"}
APPLY = "https://taleez.com/apply/"
COUNTRIES = {"FR": "France", "BE": "Belgium", "CH": "Switzerland", "DE": "Germany", "ES": "Spain",
             "GB": "United Kingdom", "IT": "Italy", "LU": "Luxembourg", "NL": "Netherlands",
             "PT": "Portugal", "US": "United States", "CA": "Canada", "MA": "Morocco", "TN": "Tunisia"}


def _tenant(url: str) -> str:
    p = urlsplit((url or "").strip())
    m = HOST.match((p.hostname or "").lower()) if p.scheme == "https" else None
    return m.group(1) if m and m.group(1) not in RESERVED else ""


def _s(v) -> str:
    return v.strip() if isinstance(v, str) else ""


class Taleez(Provider):
    name = "taleez"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("taleez.com",)

    def detect(self, careers_url: str):
        t = _tenant(careers_url)
        if not t:
            return None
        return Target(slug=t, careers_url=careers_url, api_url=f"https://{t}.taleez.com/api/careez")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        t = target.slug or _tenant(target.api_url) or _tenant(target.careers_url)
        if not t:
            raise ProviderError("taleez needs https://<tenant>.taleez.com")
        data = ctx.http.get_json(f"https://{t}.taleez.com/api/careez")
        rows = data.get("jobs") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise ProviderError("taleez: expected a site object with jobs[]")
        jobs: list[Job] = []
        for j in rows[: ctx.max_jobs]:
            if not isinstance(j, dict) or not _s(j.get("label")) or not _s(j.get("slug")):
                continue
            loc = j.get("location") if isinstance(j.get("location"), dict) else {}
            iso = _s(loc.get("country"))
            parts: list[str] = []
            for p in (_s(loc.get("city")), _s(loc.get("region")), COUNTRIES.get(iso.upper(), iso)):
                if p and p not in parts:
                    parts.append(p)
            base = ", ".join(parts)
            remote = j.get("remote") is True
            if remote and not re.search(r"\bremote\b", base, re.I):
                base = ", ".join(x for x in (base, "Remote") if x)
            posted = j.get("creationDate") if isinstance(j.get("creationDate"), (int, float)) else j.get("publishDate")
            jobs.append(self.job(
                title=j["label"], url=APPLY + quote(_s(j["slug"]), safe=""), company=target.company or t,
                location=base, country=COUNTRIES.get(iso.upper(), ""), workplace="remote" if remote else "",
                posted_at=to_iso(posted), source_id=str(j.get("id", "")),
            ).validate())
        return jobs


PROVIDER = Taleez()
