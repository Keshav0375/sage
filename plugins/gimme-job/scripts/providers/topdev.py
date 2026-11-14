"""TopDev (Vietnam IT jobs) — search result pages, board-wide.

GET https://topdev.vn/jobs/search?keyword=<kw>&page=N[&region_ids=<id>]
Upstream (career-ops scan-topdev.mjs) drives a headless browser because the cards render client side. This port
is stdlib-only: it parses whatever job cards the server-rendered HTML carries (same card structure: a
``text-card-foreground`` block with an ``/detail-jobs/`` title link, company element after it, and a
``grid-cols-2`` cell block holding location + relative age). A challenge page or a page with no cards raises
ProviderError rather than returning silently empty.
Mechanism from career-ops scan-topdev.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
import time
from urllib.parse import urlencode, urljoin, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

HOST = "topdev.vn"
SEARCH = f"https://{HOST}/jobs/search"
REGION_IDS = {"ho chi minh": "79", "hồ chí minh": "79", "hcm": "79", "hcmc": "79", "saigon": "79",
              "hanoi": "01", "ha noi": "01", "hà nội": "01", "da nang": "48", "danang": "48", "đà nẵng": "48"}
CHALLENGE = ("just a moment", "challenge-platform", "challenge-form", "cf-challenge")
UNITS = {"phút": 60, "minute": 60, "minutes": 60, "min": 60, "giờ": 3600, "hour": 3600, "hours": 3600,
         "ngày": 86400, "day": 86400, "days": 86400, "tuần": 604800, "week": 604800, "weeks": 604800,
         "tháng": 2592000, "month": 2592000, "months": 2592000}
ANCHOR = re.compile(r'<a\b[^>]*href="([^"]*/detail-jobs/[^"]*)"[^>]*>([\s\S]*?)</a>\s*(?:<(?:p|div|a|span|h\d)\b[^>]*>([\s\S]*?)</(?:p|div|a|span|h\d)>)?', re.I)


def _txt(h: str) -> str:
    import html
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", h or "")).split())


def relative_age(text: str, now: float) -> float | None:
    t = (text or "").strip().lower()
    if re.fullmatch(r"(vừa xong|just now|vừa đăng)", t):
        return now
    m = re.match(r"(\d+)\s*(minutes|minute|min|hours|hour|days|day|weeks|week|months|month|phút|giờ|ngày|tuần|tháng)(?:\s|$)", t)
    return now - int(m.group(1)) * UNITS[m.group(2)] if m else None


def parse_cards(html: str, now: float | None = None) -> list[dict]:
    now = time.time() if now is None else now
    out = []
    for chunk in re.split(r'(?=<div[^>]*class="[^"]*text-card-foreground)', html)[1:]:
        a = ANCHOR.search(chunk)
        if not a:
            continue
        href = urljoin(f"https://{HOST}", a.group(1).strip())
        p = urlsplit(href)
        title = _txt(a.group(2))
        if p.scheme != "https" or p.netloc != HOST or not title:
            continue
        grid = re.search(r'<div[^>]*grid-cols-2[^>]*>([\s\S]*?)</div>\s*</div>|<div[^>]*grid-cols-2[^>]*>([\s\S]*?)</div>', chunk)
        gtxt = (grid.group(1) or grid.group(2)) if grid else ""
        cells = [_txt(c) for c in re.findall(r"<span\b[^>]*>([\s\S]*?)</span>", gtxt)]
        cells = [c for c in cells if c]
        posted = next((relative_age(c, now) for c in cells if relative_age(c, now) is not None), None)
        out.append({"url": f"https://{HOST}{p.path}", "title": title, "company": _txt(a.group(3) or ""),
                    "location": cells[0] if cells else "", "posted": posted})
    return out


class TopDev(Provider):
    name = "topdev"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = (HOST,)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        raw = target.options.get("keywords") or target.query
        if isinstance(raw, str):
            raw = raw.replace("\n", ",").split(",")
        kws = list(dict.fromkeys(str(x).strip() for x in raw or [] if str(x).strip()))
        if not kws:
            raise ProviderError("topdev needs target.query / options.keywords")
        loc = (target.location or "").strip().lower()
        region = REGION_IDS.get(loc) if loc else None
        if loc and region is None:
            raise ProviderError(f"topdev: unknown location {target.location!r}; known: {', '.join(REGION_IDS)}")
        max_pages = min(int(target.options.get("max_pages") or 5), 50)
        now = time.time()
        jobs: dict[str, Job] = {}
        for kw in kws:
            for page in range(1, max_pages + 1):
                q = {"keyword": kw, "page": page, **({"region_ids": region} if region else {})}
                html = ctx.http.get_text(f"{SEARCH}?{urlencode(q)}")
                cards = parse_cards(html, now)
                if not cards:
                    low = html.lower()
                    if any(m in low for m in CHALLENGE):
                        raise ProviderError("topdev: challenge page served, not solved")
                    if page == 1:
                        raise ProviderError("topdev: no job cards in server HTML (rendered client side or markup changed)")
                    break
                fresh = 0
                for c in cards:
                    if c["url"] in jobs:
                        continue
                    fresh += 1
                    jobs[c["url"]] = self.job(
                        title=c["title"], url=c["url"], company=c["company"] or "TopDev",
                        location=c["location"], country="VN", posted_at=to_iso(c["posted"]) if c["posted"] else "",
                    ).validate()
                    if len(jobs) >= ctx.max_jobs:
                        return list(jobs.values())
                if not fresh:
                    break
        return list(jobs.values())


PROVIDER = TopDev()
