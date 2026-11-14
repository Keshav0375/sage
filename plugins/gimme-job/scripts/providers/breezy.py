"""Breezy HR — public JSON feed at https://<tenant>.breezy.hr/json.

Mechanism from career-ops providers/breezy.mjs (MIT).
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import employment_from, to_iso

HOST_RE = re.compile(r"^[a-z0-9][a-z0-9-]*\.breezy\.hr$")


def _origin(url: str) -> str:
    p = urlsplit(url or "")
    host = p.netloc.lower()
    return f"https://{host}" if p.scheme == "https" and HOST_RE.match(host) else ""


class Breezy(Provider):
    name = "breezy"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("breezy.hr",)

    def detect(self, careers_url: str):
        o = _origin(careers_url)
        if not o:
            return None
        return Target(slug=urlsplit(o).netloc.split(".")[0], careers_url=careers_url, api_url=f"{o}/json")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = _origin(target.api_url) or _origin(target.careers_url)
        if not o:
            raise ProviderError("breezy needs an https <tenant>.breezy.hr url")
        data = ctx.http.get_json(f"{o}/json")
        if not isinstance(data, list):
            raise ProviderError("breezy: expected an array of positions")
        company = target.company or urlsplit(o).netloc.split(".")[0]
        jobs: list[Job] = []
        for j in data:
            if not isinstance(j, dict) or not j.get("name"):
                continue
            url = str(j.get("url") or "")
            if not url.startswith("https://"):
                continue
            loc = j.get("location") or {}
            country = (loc.get("country") or {}).get("name") if isinstance(loc.get("country"), dict) else ""
            name = (loc.get("name") or "").strip()
            if name:
                base = f"{name}, {country}" if country and not re.search(rf"(?<!\w){re.escape(country)}(?!\w)", name, re.I) else name
            else:
                base = ", ".join(x for x in (loc.get("city"), loc.get("state"), country) if x)
            if loc.get("is_remote") and "remote" not in base.lower():
                base = ", ".join(x for x in (base, "Remote") if x)
            typ = j.get("type")
            jobs.append(self.job(title=str(j["name"]), url=url, company=company, location=base,
                                 workplace="remote" if loc.get("is_remote") else "",
                                 employment=employment_from(typ.get("name") if isinstance(typ, dict) else typ),
                                 department=str(j.get("department") or ""), posted_at=to_iso(j.get("published_date")),
                                 source_id=str(j.get("id") or "")).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = Breezy()
