"""PrevueAPS (Canada) — /jobs/ page gives domainId, then /core/jobs/<domainId>?getParams=...

Mechanism from career-ops providers/prevueaps.mjs (MIT); code is our own.
"""
from __future__ import annotations

import json
import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

HOST = re.compile(r"^[a-z0-9][a-z0-9-]*\.prevueaps\.ca$")
GET_PARAMS = {"showDate": True, "showLocation": True, "showEmploymentType": True, "showCategory": True,
              "showClassification": True, "showWorkplaceType": True, "customCategoryTitle": ""}
DOMAIN_RES = (r"/core/jobs/(\d+)", r"""data-domain-id\s*=\s*["'](\d+)["']""",
              r"""["']?domainId["']?\s*[:=]\s*["']?(\d+)["']?""", r"""["']?siteId["']?\s*[:=]\s*["']?(\d+)["']?""")


def _origin(url: str) -> str:
    p = urlsplit((url or "").strip())
    host = (p.hostname or "").lower()
    return f"https://{host}" if p.scheme == "https" and HOST.match(host) else ""


def _s(v) -> str:
    return v.strip() if isinstance(v, str) else ""


class PrevueAPS(Provider):
    name = "prevueaps"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("prevueaps.ca",)

    def detect(self, careers_url: str):
        o = _origin(careers_url)
        if not o:
            return None
        return Target(slug=urlsplit(o).hostname.split(".")[0], careers_url=careers_url, api_url=o + "/jobs/")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = _origin(target.careers_url) or _origin(target.api_url)
        if not o:
            raise ProviderError("prevueaps needs https://<tenant>.prevueaps.ca")
        html = ctx.http.get_text(o + "/jobs/")
        did = ""
        for rx in DOMAIN_RES:
            m = re.search(rx, html, re.I)
            if m:
                did = m.group(1)
                break
        if not did:
            raise ProviderError("prevueaps: could not resolve domainId")
        gp = quote(json.dumps(GET_PARAMS, separators=(",", ":")), safe="")
        data = ctx.http.get_json(f"{o}/core/jobs/{did}?getParams={gp}")
        rows = ((data or {}).get("data") or {}).get("jobs") if isinstance(data, dict) else None
        if not isinstance(rows, list):
            raise ProviderError("prevueaps: unexpected response, missing data.jobs")
        company = target.company or target.slug or urlsplit(o).hostname.split(".")[0]
        jobs: list[Job] = []
        for j in rows[: ctx.max_jobs]:
            if not isinstance(j, dict) or not _s(j.get("title")):
                continue
            url = _s(j.get("jobUrl"))
            if not url.startswith("https://"):
                continue
            loc = _s(j.get("jobLocation")) or ", ".join(
                x for x in (_s(j.get("city")), _s(j.get("abbreviation")) or _s(j.get("stateName"))) if x)
            bits = [_s(j.get("employmentType")), _s(j.get("classification"))]
            lo, hi = _s(j.get("minSalary")), _s(j.get("maxSalary"))
            if lo or hi:
                bits.append(" ".join(x for x in (" - ".join(x for x in (lo, hi) if x), _s(j.get("payTypeFrame"))) if x))
            jobs.append(self.job(
                title=_s(j["title"]), url=url, company=company, location=loc,
                description=" · ".join(b for b in bits if b), source_id=str(j.get("id", "")),
            ).validate())
        return jobs


PROVIDER = PrevueAPS()
