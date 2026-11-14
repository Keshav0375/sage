"""Lever — public postings API (no auth).

GET https://api.lever.co/v0/postings/{slug}   (EU tenants: api.eu.lever.co)
Mechanism from career-ops providers/lever.mjs (MIT); code is our own.
"""
from __future__ import annotations

from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso, workplace_from

_PERIOD = {"per-hour-wage": ("hour", 1), "per-month-salary": ("month", 1), "per-year-salary": ("year", 1),
           "per-day-wage": ("year", 260), "per-week-wage": ("year", 52)}


class Lever(Provider):
    name = "lever"
    wave = "W1"
    kind = "ats"
    tenant = True
    hosts = ("lever.co",)

    def detect(self, careers_url: str):
        p = urlsplit(careers_url or "")
        host = p.netloc.lower()
        if host not in ("jobs.lever.co", "jobs.eu.lever.co"):
            return None
        parts = [x for x in p.path.split("/") if x]
        if not parts:
            return None
        api_host = "api.eu.lever.co" if ".eu." in host else "api.lever.co"
        return Target(slug=parts[0], careers_url=careers_url,
                      api_url=f"https://{api_host}/v0/postings/{parts[0]}")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        t = target if target.api_url else (self.detect(target.careers_url) or target)
        api = t.api_url or (f"https://api.lever.co/v0/postings/{t.slug}" if t.slug else "")
        if not api:
            raise ProviderError("lever needs a board slug or jobs.lever.co url")
        data = ctx.http.get_json(api)
        if not isinstance(data, list):
            raise ProviderError("lever: expected a list of postings")
        jobs: list[Job] = []
        for j in data[: ctx.max_jobs]:
            cats = j.get("categories") or {}
            places: list[str] = []
            for loc in [cats.get("location")] + list(cats.get("allLocations") or []):
                if isinstance(loc, str) and loc.strip() and loc.strip() not in places:
                    places.append(loc.strip())
            wp = workplace_from(j.get("workplaceType"))
            desc = [j.get("descriptionPlain") or html_to_text(j.get("description", ""))]
            for lst in j.get("lists") or []:
                desc.append("\n".join(x for x in (lst.get("text", ""), html_to_text(lst.get("content", ""))) if x))
            desc.append(j.get("additionalPlain", ""))
            extra = {}
            sr = j.get("salaryRange") or {}
            period, mult = _PERIOD.get(sr.get("interval"), ("", 1))
            lo, hi = sr.get("min"), sr.get("max")
            if period and (lo is not None or hi is not None):
                lo = (lo if lo is not None else hi) * mult
                hi = (hi if hi is not None else lo) * mult
                extra = dict(salary_min=min(lo, hi), salary_max=max(lo, hi),
                             currency=(sr.get("currency") or "").upper(), salary_period=period)
            jobs.append(self.job(
                title=j.get("text", ""), url=j.get("hostedUrl", ""),
                company=target.company or t.slug,
                location="; ".join(places), locations=places,
                country=j.get("country") or "", workplace=wp,
                employment=_emp(cats.get("commitment")),
                department=cats.get("department") or cats.get("team") or "",
                posted_at=to_iso(j.get("createdAt")),
                description="\n\n".join(x for x in desc if x),
                source_id=str(j.get("id", "")), **extra,
            ).validate())
        return jobs


def _emp(v):
    from ._parse import employment_from
    return employment_from(v)


PROVIDER = Lever()
