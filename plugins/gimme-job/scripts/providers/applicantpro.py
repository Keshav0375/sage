"""ApplicantPro — /jobs/ page gives domainId, then /core/jobs/<domainId>?getParams={}.

Mechanism from career-ops providers/applicantpro.mjs (MIT); code is our own.
Simplified: list payload only (no per-posting JSON-LD enrichment).
"""
from __future__ import annotations

import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import parse_salary, to_iso

HOST = re.compile(r"^[a-z0-9][a-z0-9-]*\.applicantpro\.com$")
NON_TENANT = {"www", "feeds"}
TENANT = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def _origin(url: str) -> str:
    p = urlsplit((url or "").strip())
    if p.scheme != "https" or p.username or p.password:
        return ""
    host = (p.hostname or "").lower()
    if host == "www.applicantpro.com":
        m = re.match(r"^/openings/([^/]+)(?:/|$)", p.path, re.I)
        t = m.group(1).lower() if m else ""
        return f"https://{t}.applicantpro.com" if t and TENANT.match(t) and t not in NON_TENANT else ""
    if not HOST.match(host) or host.split(".")[0] in NON_TENANT:
        return ""
    return f"https://{host}"


def _s(v) -> str:
    return v.strip() if isinstance(v, str) else ""


class ApplicantPro(Provider):
    name = "applicantpro"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("applicantpro.com",)

    def detect(self, careers_url: str):
        o = _origin(careers_url)
        if not o:
            return None
        return Target(slug=urlsplit(o).hostname.split(".")[0], careers_url=careers_url, api_url=o + "/jobs/")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = _origin(target.careers_url) or _origin(target.api_url)
        if not o:
            raise ProviderError("applicantpro needs https://<tenant>.applicantpro.com")
        did = (target.options or {}).get("domainId")
        if not isinstance(did, int):
            html = ctx.http.get_text(o + "/jobs/")
            m = re.search(r"""(?<![A-Za-z0-9_])domainId["']?\s*[:=]\s*["']?(\d+)""", html) or re.search(r"/core/jobs/(\d+)", html)
            if not m:
                raise ProviderError(f"applicantpro: could not find the site id on {o}/jobs/")
            did = int(m.group(1))
        data = ctx.http.get_json(f"{o}/core/jobs/{did}?getParams={quote('{}', safe='')}")
        rows = ((data or {}).get("data") or {}).get("jobs") if isinstance(data, dict) and data.get("success") is not False else None
        if not isinstance(rows, list):
            raise ProviderError("applicantpro: unexpected response, expected data.jobs[]")
        company = target.company or target.slug or urlsplit(o).hostname.split(".")[0]
        jobs: list[Job] = []
        seen: set[str] = set()
        for r in rows:
            if not isinstance(r, dict):
                continue
            jid = str(r.get("id", "")).strip()
            title = re.sub(r"\s+", " ", r["title"]).strip() if isinstance(r.get("title"), str) else ""
            if not title or not jid.isdigit() or jid in seen:
                continue
            seen.add(jid)
            loc = _s(r.get("jobLocation")) or ", ".join(
                x for x in (_s(r.get("city")), _s(r.get("abbreviation")) or _s(r.get("stateName"))) if x)
            kw = {}
            frame = _s(r.get("payTypeFrame")).lower()
            if frame and re.search(r"year|annual", frame):
                sal = parse_salary(f"{_s(r.get('minSalary'))} - {_s(r.get('maxSalary'))} per year")
                if sal and sal.get("salary_min", 0) > 0:
                    kw = {**sal, "salary_period": "year"}
            started = _s(r.get("startDateRef"))
            jobs.append(self.job(
                title=title, url=f"{o}/jobs/{jid}", company=company, location=loc,
                posted_at=to_iso(started.replace(" ", "T") + "+00:00" if re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d", started) else started),
                source_id=jid, **kw,
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = ApplicantPro()
