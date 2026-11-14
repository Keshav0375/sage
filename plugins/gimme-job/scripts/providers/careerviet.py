"""CareerViet (VN) — server-rendered listing pages, parsed per card.

GET https://careerviet.vn/viec-lam/<keywords>-k-vi.html  (page N: ...-trang-N-vi.html)
Mechanism from career-ops providers/careerviet.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html as _html
import re
from datetime import datetime
from urllib.parse import quote, urljoin

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text

BASE = "https://careerviet.vn/viec-lam"
CARD = re.compile(r'id=["\']job-item-([A-Za-z0-9]+)["\']')
TITLE = re.compile(r'<a class=["\']job_link["\'][^>]*title=["\']([^"\']*)["\'][^>]*href=["\']([^"\']+)["\']', re.I)
COMPANY = re.compile(r'<a class=["\']company-name["\'][^>]*title=["\']([^"\']*)["\']', re.I)
LOCATION = re.compile(r'<div class=["\']location["\'][^>]*>(?:(?!</div>).)*?<li>([^<]*)</li>', re.I | re.S)
UPDATED = re.compile(r'Cập nhật(?:<!--.*?-->)?\s*:?\s*(?:</span>)?\s*<time>([\d/-]+)</time>', re.I | re.S)
HCM = {"hcm", "ho chi minh", "hồ chí minh"}


def parse_page(html: str) -> list[dict]:
    marks = list(CARD.finditer(html))
    out: dict[str, dict] = {}
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(html)
        card = html[m.start():end]
        t = TITLE.search(card)
        if not t or m.group(1) in out:
            continue
        title = _html.unescape(t.group(1)).strip()
        if not title:
            continue
        c, loc, up = COMPANY.search(card), LOCATION.search(card), UPDATED.search(card)
        posted = ""
        if up:
            try:
                posted = datetime.strptime(up.group(1).replace("/", "-"), "%d-%m-%Y").date().isoformat()
            except ValueError:
                pass
        out[m.group(1)] = {
            "id": m.group(1), "title": title,
            "url": urljoin("https://careerviet.vn", _html.unescape(t.group(2))),
            "company": _html.unescape(c.group(1)).strip() if c else "",
            "location": html_to_text(loc.group(1)) if loc else "",
            "posted": posted,
        }
    return list(out.values())


class CareerViet(Provider):
    name = "careerviet"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("careerviet.vn",)

    def _url(self, target: Target, page: int) -> str:
        kw = re.sub(r"\s+", "-", (target.query or "").strip().lower())
        city = "tai-ho-chi-minh-kl8" if (target.location or "").strip().lower() in HCM else ""
        if kw and city:
            slug = f"{quote(kw)}-{city}"
        elif kw:
            slug = f"{quote(kw)}-k"
        else:
            slug = "tat-ca-viec-lam"
        return f"{BASE}/{slug}" + ("-vi.html" if page <= 1 else f"-trang-{page}-vi.html")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        pages = min(int(target.options.get("max_pages") or 3), 50)
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(1, pages + 1):
            url = self._url(target, page)
            html = ctx.http.get_text(url)
            cards = parse_page(html)
            if not cards:
                if page == 1 and CARD.search(html):
                    raise ProviderError("careerviet: job cards present but none parsed (markup changed)")
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


PROVIDER = CareerViet()
