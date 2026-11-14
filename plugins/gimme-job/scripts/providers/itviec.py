"""ITviec (VN) — server-rendered listing cards keyed by a job-slug data attribute.

GET https://itviec.com/it-jobs[/<keywords>][/<city>][?page=N]
Mechanism from career-ops providers/itviec.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html as _html
import re
from datetime import date, timedelta
from urllib.parse import quote

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text

LIST_URL = "https://itviec.com/it-jobs"
CARD = re.compile(r"""data-search--job-selection-job-slug-value=['"]([^'"]+)['"]""", re.I)
TITLE = re.compile(r"""<h3[^>]*data-search--job-selection-target=['"]jobTitle['"][^>]*>\s*<a[^>]*>(.*?)</a>""", re.I | re.S)
COMPANY = re.compile(r"""href=["'](?:https?://itviec\.com)?/companies/[^"']+["'][^>]*>(.*?)</a>""", re.I | re.S)
LOCATION = re.compile(r"""#map-pin"?></use></svg>\s*<div[^>]*title=['"]([^'"]*)['"]""", re.I)
POSTED = re.compile(r"(?:Posted|Đăng)\s*:?\s*(?:</\w+>\s*)?([^.<]{0,40}?(?:ago|trước)|today|hôm nay)", re.I)
CITIES = {"hcm": "ho-chi-minh-hcm", "ho chi minh": "ho-chi-minh-hcm", "hanoi": "ha-noi", "ha noi": "ha-noi",
          "danang": "da-nang", "da nang": "da-nang"}


def posted_date(text: str, today: date) -> str:
    t = (text or "").lower()
    if "today" in t or "hôm nay" in t:
        return today.isoformat()
    for pat, days in ((r"(\d+)\s*(?:hour|giờ)", 0), (r"(\d+)\s*(?:day|ngày)", 1),
                      (r"(\d+)\s*(?:week|tuần)", 7), (r"(\d+)\s*(?:month|tháng)", 30)):
        m = re.search(pat, t)
        if m:
            return (today - timedelta(days=int(m.group(1)) * days)).isoformat()
    return ""


def parse_page(html: str) -> list[dict]:
    marks = list(CARD.finditer(html))
    out: dict[str, dict] = {}
    today = date.today()
    for i, m in enumerate(marks):
        slug = m.group(1)
        if slug in out:
            continue
        card = html[m.start(): marks[i + 1].start() if i + 1 < len(marks) else len(html)]
        t = TITLE.search(card)
        title = html_to_text(t.group(1)) if t else ""
        if not title:
            continue
        company = ""
        for cm in COMPANY.finditer(card):
            company = html_to_text(cm.group(1))
            if company:
                break
        loc, p = LOCATION.search(card), POSTED.search(card)
        out[slug] = {"title": title, "url": f"{LIST_URL}/{slug}", "company": company,
                     "location": _html.unescape(loc.group(1)).strip() if loc else "",
                     "posted": posted_date(p.group(0), today) if p else "", "id": slug}
    return list(out.values())


class ITviec(Provider):
    name = "itviec"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("itviec.com",)

    def _url(self, target: Target, page: int) -> str:
        path = LIST_URL
        kw = re.sub(r"\s+", "-", (target.query or "").strip().lower()).replace("/", "")
        if kw:
            path += "/" + quote(kw)
        city = CITIES.get((target.location or "").strip().lower())
        if city:
            path += "/" + city
        return path if page <= 1 else f"{path}?page={page}"

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        pages = min(int(target.options.get("max_pages") or 3), 50)
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(1, pages + 1):
            html = ctx.http.get_text(self._url(target, page))
            cards = parse_page(html)
            if not cards:
                if page == 1 and re.search(r"""href=["'](?:https?://itviec\.com)?/it-jobs/[a-z0-9-]+-\d+""", html, re.I):
                    raise ProviderError("itviec: job links present but no card parsed (markup changed)")
                break
            fresh = 0
            for c in cards:
                if c["url"] in seen:
                    continue
                seen.add(c["url"])
                fresh += 1
                jobs.append(self.job(title=c["title"], url=c["url"], company=c["company"],
                                     location=c["location"], country="VN", posted_at=c["posted"],
                                     source_id=c["id"]).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if not fresh:
                break
        return jobs


PROVIDER = ITviec()
