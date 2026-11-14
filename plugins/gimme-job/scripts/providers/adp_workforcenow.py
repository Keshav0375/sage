"""ADP WorkforceNow career center — public staffing events API (job-requisitions).

https://workforcenow.adp.com/mascsr/default/careercenter/public/events/staffing/v1/job-requisitions?cid=..&ccId=..
Mechanism from career-ops providers/adp-workforcenow.mjs (MIT); list path only.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlencode, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

HOST = "workforcenow.adp.com"
API = f"https://{HOST}/mascsr/default/careercenter/public/events/staffing/v1/job-requisitions"
PAGE_SIZE = 20
MAX_PAGES = 100


def _tenant(url: str):
    p = urlsplit(url or "")
    if p.scheme != "https" or p.netloc.lower() != HOST:
        return None
    q = parse_qs(p.query)
    cid, cc = (q.get("cid") or [""])[0], (q.get("ccId") or [""])[0]
    if not cid or not cc:
        return None
    return {"cid": cid, "ccId": cc, "lang": (q.get("lang") or ["en_US"])[0]}


def _field(group, key: str, code: str):
    for f in (group or {}).get(key) or []:
        if ((f or {}).get("nameCode") or {}).get("codeValue") == code:
            return f
    return None


def _location(job: dict) -> str:
    out: list[str] = []
    for loc in job.get("requisitionLocations") or []:
        nc = (loc or {}).get("nameCode") or {}
        label = str(nc.get("shortName") or nc.get("longName") or "").strip()
        if not label:
            a = (loc or {}).get("address") or {}
            label = ", ".join(x for x in (str(a.get("cityName") or "").strip(),
                                          str(((a.get("countrySubdivisionLevel1") or {}).get("codeValue")) or "").strip(),
                                          str(((a.get("country") or {}).get("codeValue")) or "").strip()) if x)
        if label and label not in out:
            out.append(label)
    return " / ".join(out)


def _salary(job: dict) -> dict:
    sr = (_field(job.get("customFieldGroup"), "stringFields", "SalaryRange") or {}).get("stringValue")
    if isinstance(sr, str) and re.search(r"(?i)\bhour(?:ly)?\b|\bper\s+hour\b", sr):
        return {}
    rng = job.get("payGradeRange") or {}
    lo = ((rng.get("minimumRate") or {}).get("amountValue"))
    hi = ((rng.get("maximumRate") or {}).get("amountValue"))
    lo = lo if isinstance(lo, (int, float)) else None
    hi = hi if isinstance(hi, (int, float)) else None
    if lo is None and hi is None:
        return {}
    cur = (rng.get("minimumRate") or {}).get("currencyCode") or (rng.get("maximumRate") or {}).get("currencyCode") or ""
    return {"salary_min": lo, "salary_max": hi, "currency": cur if isinstance(cur, str) else ""}


class AdpWorkforceNow(Provider):
    name = "adp-workforcenow"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = (HOST,)

    def detect(self, careers_url: str):
        t = _tenant(careers_url)
        if not t:
            return None
        return Target(slug=t["cid"], careers_url=careers_url,
                      api_url=f"{API}?{urlencode({'cid': t['cid'], 'ccId': t['ccId'], '$skip': 1, '$top': PAGE_SIZE, 'lang': t['lang'], 'locale': t['lang']})}")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        t = _tenant(target.api_url) or _tenant(target.careers_url)
        if not t:
            raise ProviderError("adp-workforcenow needs a workforcenow.adp.com url with cid and ccId")
        company = target.company or t["cid"]
        jobs: list[Job] = []
        seen: set[str] = set()
        skip = 1
        for _ in range(MAX_PAGES):
            q = urlencode({"cid": t["cid"], "ccId": t["ccId"], "$skip": skip, "$top": PAGE_SIZE, "lang": t["lang"], "locale": t["lang"]})
            data = ctx.http.get_json(f"{API}?{q}")
            if not isinstance(data, dict) or (not isinstance(data.get("jobRequisitions"), list) and not isinstance(data.get("meta"), dict)):
                raise ProviderError("adp-workforcenow: unrecognized job-requisitions response")
            raw = data.get("jobRequisitions") or []
            if not raw:
                break
            fresh = 0
            for j in raw:
                item = str(j.get("itemID") or "").strip()
                title = str(j.get("requisitionTitle") or "").strip()
                if not item or not title or item in seen:
                    continue
                seen.add(item)
                fresh += 1
                ext = str((_field(j.get("customFieldGroup"), "stringFields", "ExternalJobID") or {}).get("stringValue") or "").strip()
                url = "https://" + HOST + "/mascsr/default/mdf/recruitment/recruitment.html?" + urlencode(
                    {"cid": t["cid"], "ccId": t["ccId"], "lang": "en_US", "type": "JS", "jobId": ext or item, "jwId": item})
                posted = to_iso(j.get("postDate")) or to_iso((_field(j.get("customFieldGroup"), "dateFields", "PostingDate") or {}).get("dateValue"))
                jobs.append(self.job(title=title, url=url, company=company, location=_location(j), posted_at=posted,
                                     source_id=item, **_salary(j)).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if not fresh or len(raw) < PAGE_SIZE:
                break
            skip += len(raw)
        return jobs


PROVIDER = AdpWorkforceNow()
