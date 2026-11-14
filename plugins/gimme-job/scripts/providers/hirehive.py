"""HireHive — public jobs API https://<tenant>.hirehive.com/api/v2/jobs?page=&page_size=100.

Mechanism from career-ops providers/hirehive.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

HOST = re.compile(r"^([a-z0-9](?:[a-z0-9-]*[a-z0-9])?)\.hirehive\.com$")
VENDOR = {"www", "app", "accounts", "apply"}
PAGE_SIZE = 100
MAX_PAGES = 20


def _tenant_of_host(host: str) -> str:
    m = HOST.match((host or "").lower())
    return m.group(1) if m and m.group(1) not in VENDOR else ""


def _tenant(url: str) -> str:
    p = urlsplit((url or "").strip())
    return _tenant_of_host(p.hostname or "") if p.scheme == "https" else ""


def _s(v) -> str:
    return v.strip() if isinstance(v, str) else ""


def _pos(v):
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    return n if n > 0 else None


class HireHive(Provider):
    name = "hirehive"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("hirehive.com",)

    def detect(self, careers_url: str):
        t = _tenant(careers_url)
        if not t:
            return None
        return Target(slug=t, careers_url=careers_url, api_url=f"https://{t}.hirehive.com/api/v2/jobs")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        t = target.slug or _tenant(target.careers_url) or _tenant(target.api_url)
        if not t:
            raise ProviderError("hirehive needs https://<tenant>.hirehive.com")
        origin = f"https://{t}.hirehive.com"
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(1, MAX_PAGES + 1):
            data = ctx.http.get_json(f"{origin}/api/v2/jobs?page={page}&page_size={PAGE_SIZE}")
            rows = data.get("items") if isinstance(data, dict) else None
            if not isinstance(rows, list):
                raise ProviderError("hirehive: unexpected response, expected items[]")
            for r in rows:
                if not isinstance(r, dict):
                    continue
                url = _s(r.get("hosted_url"))
                if not _s(r.get("title")) or not _tenant(url) or url in seen:
                    continue
                seen.add(url)
                text, country = _s(r.get("location")), _s((r.get("country") or {}).get("name"))
                loc = text if (not country or country.lower() in text.lower()) else (f"{text}, {country}" if text else country)
                kw = {}
                for tier in r.get("compensation_tiers") or []:
                    if not isinstance(tier, dict) or tier.get("type") not in ("range_salary", "fixed_salary") \
                            or tier.get("interval") != "year":
                        continue
                    lo, hi = _pos(tier.get("min_value")), _pos(tier.get("max_value"))
                    if lo or hi:
                        lo, hi = lo or hi, hi or lo
                        kw = dict(salary_min=min(lo, hi), salary_max=max(lo, hi), salary_period="year",
                                  currency=_s(tier.get("currency_code")).upper())
                        break
                desc = r.get("description") or {}
                jobs.append(self.job(
                    title=r["title"], url=url, company=target.company or t, location=loc,
                    posted_at=to_iso(r.get("published_date")),
                    description=html_to_text(_s(desc.get("html"))) or _s(desc.get("text")),
                    source_id=str(r.get("id", "")), **kw,
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            has_next = (data.get("meta") or {}).get("has_next_page") is not False
            if not has_next or len(rows) < PAGE_SIZE:
                break
        return jobs


PROVIDER = HireHive()
