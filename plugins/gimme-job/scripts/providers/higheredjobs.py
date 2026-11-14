"""HigherEdJobs (US academia) — category RSS feed, board-wide.

GET https://www.higheredjobs.com/rss/categoryFeed.cfm?catID=<id>   (default 68, options.cat_id)
Mechanism from career-ops providers/higheredjobs.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import feed_items, to_iso

HOST = "www.higheredjobs.com"


def split_description(desc: str) -> tuple[str, str]:
    t = desc.strip()
    i = t.rfind(" (")
    if i > 0:
        j = t.rfind(")")
        company = t[:i].strip()
        if company:
            return company, (t[i + 2:j] if j > i else t[i + 2:]).strip()
    return t, ""


class HigherEdJobs(Provider):
    name = "higheredjobs"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = (HOST,)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        cat = target.options.get("cat_id") or 68
        text = ctx.http.get_text(f"https://{HOST}/rss/categoryFeed.cfm?catID={int(cat)}")
        if not re.search(r"<(?:rss|channel)\b", text, re.I):
            raise ProviderError("higheredjobs: endpoint answered no RSS feed")
        out: list[Job] = []
        for it in feed_items(text):
            p = urlsplit((it.get("link") or "").strip())
            if p.scheme != "https" or p.netloc.lower() != HOST or not it.get("title"):
                continue
            company, loc = split_description(it.get("description", ""))
            out.append(self.job(title=it["title"], url=it["link"].strip(), company=company or "HigherEdJobs",
                                location=loc, country="US", posted_at=to_iso(it.get("published"))).validate())
            if len(out) >= ctx.max_jobs:
                break
        return out


PROVIDER = HigherEdJobs()
