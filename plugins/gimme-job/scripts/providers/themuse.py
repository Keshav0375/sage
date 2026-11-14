"""The Muse — server-rendered search pages (public, no auth).

GET https://www.themuse.com/search?q=..&location=..&category=..&remote=1&posted=7[&page=N]
Cards: <article class="sr-tile" data-job-id> with h2.sr-tile__title > a[/jobs/{company}/{slug}], a[/profiles/..], details <p>s.
Mechanism from career-ops providers/themuse.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html
import re
from datetime import datetime, timezone
from urllib.parse import urlencode

from ._base import Context, Job, Provider, ProviderError, Target

HOST = "www.themuse.com"
SEARCH = f"https://{HOST}/search"
PAGE_SIZE = 20

CARD_OPEN = re.compile(r'<article\b[^>]*class="[^"]*\bsr-tile\b[^"]*"[^>]*>')
JOB_ID = re.compile(r'data-job-id="([^"]+)"')
TITLE_LINK = re.compile(r'<h2\b[^>]*class="[^"]*\bsr-tile__title\b[^"]*"[^>]*>\s*<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S)
PROFILE = re.compile(r'<a\b[^>]*href="(/profiles/[^"]*)"[^>]*>(.*?)</a>', re.S)
DETAILS = re.compile(r'<div\b[^>]*class="[^"]*\bsr-tile__details\b[^"]*"[^>]*>(.*?)</div>', re.S)
PARA = re.compile(r"<p>(.*?)</p>", re.S)
COUNT = re.compile(r'<h1\b[^>]*class="[^"]*\bsr-count\b[^"]*"[^>]*>(.*?)</h1>', re.S)
POSTED = re.compile(r"Posted on\s+([A-Za-z]+)\s+(\d{1,2})")
JOB_HREF = re.compile(r"^/jobs/[^/?#\s]+/[^/?#\s]+$")
MONTHS = {m: i + 1 for i, m in enumerate(["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"])}


def _clean(s: str) -> str:
    s = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", s))).strip()


def _posted(text: str, now: datetime) -> str:
    m = POSTED.search(text or "")
    if not m or m.group(1)[:3].lower() not in MONTHS:
        return ""
    mon, day = MONTHS[m.group(1)[:3].lower()], int(m.group(2))
    try:
        d = datetime(now.year, mon, day, tzinfo=timezone.utc)
        if d > now:
            d = d.replace(year=now.year - 1)
    except ValueError:
        return ""
    return d.date().isoformat()


def parse_page(page_html: str, location: str = "", now: datetime | None = None):
    now = now or datetime.now(timezone.utc)
    cm = COUNT.search(page_html or "")
    if not cm:
        raise ProviderError("themuse: layout change - no h1.sr-count")
    digits = re.search(r"\d+", _clean(cm.group(1)).replace(",", ""))
    if not digits:
        raise ProviderError("themuse: layout change - no job count")
    total = int(digits.group(0))
    starts = [m.start() for m in CARD_OPEN.finditer(page_html)]
    if total > 0 and not starts:
        raise ProviderError("themuse: layout change - no job cards")
    rows = []
    for i, s in enumerate(starts):
        nxt = starts[i + 1] if i + 1 < len(starts) else len(page_html)
        close = page_html.find("</article>", s)
        seg = page_html[s: nxt if close == -1 else min(close + 10, nxt)]
        tm = TITLE_LINK.search(seg)
        if not tm:
            continue
        href = html.unescape(tm.group(1)).strip()
        title = _clean(tm.group(2))
        if not JOB_HREF.match(href) or not title:
            continue
        pm = PROFILE.search(seg)
        loc, posted = "", ""
        dm = DETAILS.search(seg)
        if dm:
            paras = PARA.findall(dm.group(1))
            if paras:
                first = _clean(paras[0])
                d = first.rfind(" - ")
                loc = first[d + 3:].strip() if d != -1 else ""
                if loc == "Remote / Flexible" and location:
                    loc = f"Remote / Flexible, {location}"
            pp = next((p for p in paras if "Posted on" in p), None)
            if pp:
                posted = _posted(_clean(pp), now)
        idm = JOB_ID.search(seg)
        rows.append({"title": title, "url": f"https://{HOST}{href}", "company": _clean(pm.group(2)) if pm else "",
                     "location": loc, "posted_at": posted, "id": idm.group(1) if idm else ""})
    return total, rows


class TheMuse(Provider):
    name = "themuse"
    wave = "W3"
    kind = "board"
    tenant = False
    hosts = (HOST,)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = target.options
        params = {}
        if target.location:
            params["location"] = target.location
        if target.query:
            params["q"] = target.query
        if o.get("category"):
            params["category"] = o["category"]
        if o.get("remote"):
            params["remote"] = "1"
        if o.get("posted") in (1, 7, 30, "1", "7", "30"):
            params["posted"] = str(o["posted"])
        max_pages = min(int(o.get("max_pages") or 100), 1500)
        jobs: list[Job] = []
        total = None
        page = 1
        while page <= max_pages:
            q = dict(params)
            if page > 1:
                q["page"] = page
            url = SEARCH + ("?" + urlencode(q) if q else "")
            t, rows = parse_page(ctx.http.get_text(url), target.location)
            if total is None:
                total = t
            for r in rows:
                jobs.append(self.job(
                    title=r["title"], url=r["url"], company=r["company"], location=r["location"],
                    workplace="remote" if r["location"].lower() == "remote" else "",
                    posted_at=r["posted_at"], source_id=r["id"],
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if not rows or page >= -(-total // PAGE_SIZE):
                break
            page += 1
        return jobs


PROVIDER = TheMuse()
