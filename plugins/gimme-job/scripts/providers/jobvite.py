"""Jobvite — public XML feed at app.jobvite.com/CompanyJobs/Xml.aspx?c=<companyEId>.

The company id is read from the board page (jobs.jobvite.com/<slug>) unless options.company_eid is given.
Mechanism from career-ops providers/jobvite.mjs (MIT).
"""
from __future__ import annotations

import html
from datetime import datetime
import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

BOARD = "jobs.jobvite.com"
FEED = "app.jobvite.com"


def _tag(block: str, name: str) -> str:
    m = re.search(rf"<{name}>(.*?)</{name}>", block, re.S)
    if not m:
        return ""
    v = m.group(1).strip()
    if v.startswith("<![CDATA[") and v.endswith("]]>"):
        v = v[9:-3].strip()
    return v


def _date(v: str) -> str:
    try:
        return datetime.strptime(v.strip(), "%m/%d/%Y").date().isoformat()
    except ValueError:
        return to_iso(v)


def _slug(url: str) -> str:
    p = urlsplit(url or "")
    if p.scheme != "https" or p.netloc.lower() != BOARD:
        return ""
    segs = [s for s in p.path.split("/") if s]
    return segs[0] if segs and segs[0] != "api" else ""


def parse_feed(xml: str, company: str) -> list[dict]:
    out: dict[str, dict] = {}
    for m in re.finditer(r"<job>(.*?)</job>", xml or "", re.S):
        b = m.group(1)
        title = html.unescape(_tag(b, "title"))
        url = ""
        for c in (_tag(b, "detail-url"), _tag(b, "apply-url")):
            c = html.unescape(c)
            if c.startswith(("http://", "https://")):
                url = re.sub(r"^http://", "https://", c)
                break
        if not title or not url:
            continue
        loc = html.unescape(_tag(b, "location"))
        if url in out:
            if loc and loc not in out[url]["locations"]:
                out[url]["locations"].append(loc)
            continue
        out[url] = {"title": title, "url": url, "locations": [loc] if loc else [], "date": _tag(b, "date"),
                    "id": _tag(b, "id"), "dept": html.unescape(_tag(b, "category") or _tag(b, "department"))}
    return list(out.values())


class Jobvite(Provider):
    name = "jobvite"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("jobvite.com",)

    def detect(self, careers_url: str):
        slug = _slug(careers_url)
        if not slug:
            return None
        return Target(slug=slug, careers_url=careers_url, api_url=f"https://{BOARD}/{quote(slug)}")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        eid = str(target.options.get("company_eid") or "").strip()
        if not eid:
            m = re.search(r"[?&]c=([\w-]+)", target.api_url or "") if FEED in (target.api_url or "") else None
            eid = m.group(1) if m else ""
        if not eid:
            slug = target.slug or _slug(target.careers_url)
            if not slug:
                raise ProviderError("jobvite needs a jobs.jobvite.com url or options.company_eid")
            page = ctx.http.get_text(f"https://{BOARD}/{quote(slug)}?fr=true&nl=1")
            m = re.search(r"""companyEId\s*[:=]\s*['"]([A-Za-z0-9_-]{4,40})['"]""", page)
            if not m:
                raise ProviderError(f"jobvite: companyEId not found for {slug}")
            eid = m.group(1)
        xml = ctx.http.get_text(f"https://{FEED}/CompanyJobs/Xml.aspx?c={quote(eid)}")
        company = target.company or target.slug
        jobs = []
        for r in parse_feed(xml, company)[: ctx.max_jobs]:
            jobs.append(self.job(title=r["title"], url=r["url"], company=company, locations=r["locations"],
                                 location=" · ".join(r["locations"]), posted_at=_date(r["date"]),
                                 department=r["dept"], source_id=r["id"]).validate())
        return jobs


PROVIDER = Jobvite()
