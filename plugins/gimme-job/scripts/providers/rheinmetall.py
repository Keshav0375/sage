"""Rheinmetall — server-rendered vacancy cards at www.rheinmetall.com/en/career/vacancies?page=N.

Mechanism from career-ops providers/rheinmetall.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html
import re
from urllib.parse import unquote, urlsplit

from ._base import Context, Job, Provider, Target

MAX_PAGES = 150
DEFAULT_LIST = "https://www.rheinmetall.com/en/career/vacancies"


def _clean(s: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", s)).split())


def _is_rm(url: str) -> bool:
    h = urlsplit(url or "").netloc.lower()
    return h == "rheinmetall.com" or h.endswith(".rheinmetall.com")


class Rheinmetall(Provider):
    name = "rheinmetall"
    wave = "W6"
    kind = "company"
    tenant = False
    hosts = ("rheinmetall.com",)

    def detect(self, careers_url: str):
        return Target(careers_url=careers_url) if _is_rm(careers_url) else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        list_url = DEFAULT_LIST
        if _is_rm(target.careers_url):
            p = urlsplit(target.careers_url)
            host = "www.rheinmetall.com" if p.netloc.lower() == "rheinmetall.com" else p.netloc
            if re.search(r"/career/vacancies/?$", p.path):
                list_url = f"https://{host}{p.path.rstrip('/')}"
        origin = "https://" + urlsplit(list_url).netloc
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(1, MAX_PAGES + 1):
            body = ctx.http.get_text(f"{list_url}?page={page}", headers={"Accept": "text/html"})
            fresh = 0
            for block in re.split(r'<div class="flex gap-0\.5 group">', body)[1:]:
                link = re.search(r'href="(/[a-z]{2}/job/[^"]+/(\d+))"', block)
                if not link or link.group(2) in seen:
                    continue
                tm = re.search(r'md:text-xl[^"]*">([\s\S]*?)</div>', block)
                if tm:
                    title = _clean(tm.group(1))
                else:
                    parts = link.group(1).split("/")
                    title = _clean(unquote(parts[3] if len(parts) > 3 else "").replace("_", " "))
                if not title:
                    continue
                om = re.search(r'class="flex flex-wrap mr-6">([\s\S]*?)</div>', block)
                org = _clean(om.group(1)) if om else ""
                city = org.split("|")[-1].strip() if "|" in org else ""
                seen.add(link.group(2))
                fresh += 1
                jobs.append(self.job(title=title, url=origin + link.group(1),
                                     company=target.company or "Rheinmetall", location=city,
                                     source_id=link.group(2)).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if not fresh:
                break
        return jobs


PROVIDER = Rheinmetall()
