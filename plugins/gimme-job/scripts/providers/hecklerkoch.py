"""Heckler & Koch — SSR vacancy list linking to karriere.heckler-koch.com/jobposting/<id>.

Mechanism from career-ops providers/hecklerkoch.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html
import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, Target

DEFAULT_LIST = "https://www.heckler-koch.com/de/Karriere/Stellenangebote"
ANCHOR_RE = re.compile(r'<a\b[^>]*href="(https://karriere\.heckler-koch\.com/jobposting/([a-z0-9]+))"[\s\S]*?</a>', re.I)


def _is_hk(url: str) -> bool:
    h = urlsplit(url or "").netloc.lower()
    return h == "heckler-koch.com" or h.endswith(".heckler-koch.com")


class HecklerKoch(Provider):
    name = "hecklerkoch"
    wave = "W6"
    kind = "company"
    tenant = False
    hosts = ("heckler-koch.com",)

    def detect(self, careers_url: str):
        return Target(careers_url=careers_url) if _is_hk(careers_url) else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        raw = target.careers_url
        list_url = DEFAULT_LIST
        if _is_hk(raw) and re.search("Stellenangebote", urlsplit(raw).path, re.I):
            p = urlsplit(raw)
            host = "www.heckler-koch.com" if p.netloc.lower() == "heckler-koch.com" else p.netloc
            list_url = f"https://{host}{p.path}"
        page = ctx.http.get_text(list_url, headers={"Accept": "text/html"})
        jobs, seen = [], set()
        for m in ANCHOR_RE.finditer(page):
            jid = m.group(2)
            t = re.search(r"<h3\b[^>]*>([\s\S]*?)</h3>", m.group(0), re.I)
            title = " ".join(html.unescape(re.sub(r"<[^>]*>", " ", t.group(1))).split()) if t else ""
            if not title or jid in seen:
                continue
            seen.add(jid)
            jobs.append(self.job(title=title, url=html.unescape(m.group(1)),
                                 company=target.company or "Heckler & Koch", source_id=jid).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = HecklerKoch()
