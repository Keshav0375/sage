"""Recruitee — public offers API (no auth).

GET https://{slug}.recruitee.com/api/offers/
Mechanism from career-ops providers/recruitee.mjs (MIT); code is our own.
Simplified: one posting per offer (no per-language fan-out).
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import employment_from, html_to_text, to_iso

HOST_RE = re.compile(r"^([a-z0-9][a-z0-9-]*)\.recruitee\.com$")
_MULT = {"hour": 2080, "month": 12, "year": 1}


class Recruitee(Provider):
    name = "recruitee"
    wave = "W1"
    kind = "ats"
    tenant = True
    hosts = ("recruitee.com",)

    def detect(self, careers_url: str):
        host = urlsplit(careers_url or "").netloc.lower()
        m = HOST_RE.match(host)
        if not m or m.group(1) in ("www", "api"):
            return None
        return Target(slug=m.group(1), careers_url=careers_url, api_url=f"https://{host}/api/offers/")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        slug = target.slug or (self.detect(target.careers_url) or Target()).slug
        if not slug:
            raise ProviderError("recruitee needs a company slug")
        data = ctx.http.get_json(target.api_url or f"https://{slug}.recruitee.com/api/offers/")
        if not isinstance(data, dict) or not isinstance(data.get("offers"), list):
            raise ProviderError("recruitee: expected {offers: [...]}")
        jobs: list[Job] = []
        for o in data["offers"][: ctx.max_jobs]:
            if o.get("status") not in (None, "published") or not (o.get("title") or "").strip():
                continue
            places = []
            for l in o.get("locations") or []:
                parts = [l.get("name") or l.get("city"), l.get("country")]
                s = ", ".join(x for x in parts if x)
                if s and s not in places:
                    places.append(s)
            if not places:
                s = ", ".join(x for x in (o.get("city"), o.get("country")) if x)
                places = [s] if s else []
            sal, extra = o.get("salary"), {}
            if isinstance(sal, dict) and sal.get("period") in _MULT and (sal.get("min") or sal.get("max")):
                lo = float(sal.get("min") or sal.get("max"))
                hi = float(sal.get("max") or sal.get("min"))
                extra = dict(salary_min=min(lo, hi), salary_max=max(lo, hi),
                             currency=(sal.get("currency") or "").upper(), salary_period=sal["period"])
            jobs.append(self.job(
                title=o.get("title", ""), url=o.get("careers_url") or o.get("url") or "",
                company=target.company or o.get("company_name") or slug,
                locations=places, country=o.get("country") or "",
                workplace="remote" if o.get("remote") else "",
                employment=employment_from(o.get("employment_type_code")),
                department=o.get("department") or "",
                posted_at=to_iso(o.get("published_at")),
                description=html_to_text(o.get("description", "")),
                source_id=str(o.get("id", "")), **extra,
            ).validate())
        return jobs


PROVIDER = Recruitee()
