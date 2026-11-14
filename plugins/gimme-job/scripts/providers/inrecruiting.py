"""InRecruiting (Intervieweb, Italy) — https://<tenant>.intervieweb.it/<lang>/career card list + AJAX paging.

Mechanism from career-ops providers/inrecruiting.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html as htmllib
import json
import re
from urllib.parse import urlencode, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

HOST = re.compile(r"^[a-z0-9][a-z0-9-]*\.intervieweb\.it$")
NON_TENANT = {"inrecruiting.intervieweb.it", "www.intervieweb.it"}
MAX_PAGES = 40
CARD = re.compile(r"""<a[^>]+href=["'](https://[a-z0-9-]+\.intervieweb\.it/jobs/[^"'#?]+)["'][^>]*>\s*<h3[^>]*>([\s\S]*?)</h3>""", re.I)
POSTING = re.compile(r"""href=["']https://[a-z0-9-]+\.intervieweb\.it/jobs/[^"']+-\d+/[a-z]{2}/?["']""", re.I)
LOCATION = re.compile(r"""mi-location_on[\s\S]*?</i>\s*(?:<span[^>]*sr-only[^>]*>[\s\S]*?</span>)?([\s\S]*?)</span>""", re.I)
ANNOUNCES = re.compile(r"""id=["']url-for-announces["'][^>]*value=["']([^"']+)["']""", re.I)
SECTION = re.compile(r"""['"]section['"]\s*:\s*['"]([A-Za-z0-9_-]+)['"]""")
NEXT = re.compile(r"""pagination_next["'][^>]*onclick=["']researchAnnounces\(\s*(\d+)\s*,\s*'([a-z_]+)'""", re.I)


def _tenant(url: str):
    p = urlsplit((url or "").strip())
    host = (p.hostname or "").lower()
    if p.scheme != "https" or not HOST.match(host) or host in NON_TENANT:
        return None
    m = re.match(r"^/([a-z]{2})/career\b", p.path) or re.match(r"^/jobs/[^/]+/([a-z]{2})/?$", p.path)
    return host, (m.group(1) if m else "it")


def _text(h: str) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", h or ""))).strip()


def _cards(html: str, host: str) -> list[tuple[str, str, str]]:
    ms = list(CARD.finditer(html))
    rows = []
    for i, m in enumerate(ms):
        url = htmllib.unescape(m.group(1))
        if urlsplit(url).hostname != host:
            continue
        title = _text(m.group(2))
        if not title:
            continue
        end = ms[i + 1].start() if i + 1 < len(ms) else len(html)
        lm = LOCATION.search(html[m.start():end])
        rows.append((title, url, _text(lm.group(1)) if lm else ""))
    return rows


class InRecruiting(Provider):
    name = "inrecruiting"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("intervieweb.it",)

    def detect(self, careers_url: str):
        t = _tenant(careers_url)
        if not t:
            return None
        return Target(slug=t[0].split(".")[0], careers_url=careers_url, api_url=f"https://{t[0]}/{t[1]}/career")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        t = _tenant(target.api_url) or _tenant(target.careers_url)
        if not t:
            raise ProviderError("inrecruiting needs https://<tenant>.intervieweb.it/<lang>/career")
        host, lang = t
        career = f"https://{host}/{lang}/career"
        html = ctx.http.get_text(career)
        first = _cards(html, host)
        if not first:
            if POSTING.search(html):
                raise ProviderError("inrecruiting: page links postings but none could be parsed")
            if not ANNOUNCES.search(html):
                raise ProviderError("inrecruiting: not an InRecruiting career page")
            return []
        company = target.company or host.split(".")[0]
        jobs: list[Job] = []
        seen: set[str] = set()

        def push(rows) -> None:
            for title, url, loc in rows:
                if url in seen:
                    continue
                seen.add(url)
                jobs.append(self.job(title=title, url=url, company=company, location=loc,
                                     source_id=url.rstrip("/").split("/")[-2] if POSTING.search(f'href="{url}"') else "").validate())

        push(first)
        nxt = NEXT.search(html)
        um, sm = ANNOUNCES.search(html), SECTION.search(html)
        announce = ""
        if um:
            u = urlsplit(htmllib.unescape(um.group(1)))
            if u.scheme == "https" and u.hostname == host and u.path == "/app.php":
                announce = f"https://{host}/app.php" + (f"?{u.query}" if u.query else "")
        fetched = 1
        while nxt and announce and sm and fetched < MAX_PAGES and len(jobs) < ctx.max_jobs:
            page, order = int(nxt.group(1)), nxt.group(2)
            body = urlencode({"act1": "vacancyListCareer", "section": sm.group(1), "order": order, "page": page,
                              "country": "", "region": "", "function": "", "project": "", "text": "",
                              "division": "", "company": ""})
            resp = ctx.http.post(announce, data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})
            try:
                j = json.loads(resp.text)
            except ValueError:
                raise ProviderError("inrecruiting: pagination response is not JSON")
            if not isinstance(j, dict) or j.get("success") is not True or not isinstance(j.get("data"), str):
                raise ProviderError("inrecruiting: unexpected pagination response")
            fetched += 1
            rows = _cards(j["data"], host)
            if not rows:
                break
            push(rows)
            following = NEXT.search(j["data"])
            nxt = following if following and int(following.group(1)) > page else None
        return jobs[: ctx.max_jobs]


PROVIDER = InRecruiting()
