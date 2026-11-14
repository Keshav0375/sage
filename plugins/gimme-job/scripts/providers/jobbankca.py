"""Job Bank Canada — public Atom search feed (no auth).

GET https://www.jobbank.gc.ca/jobsearch/feed/jobSearchRSSfeed?searchstring=<kw>&page=N
Mechanism from career-ops providers/jobbankca.mjs (MIT); code is our own.
Keywords: Target.query (comma separated) or Target.options["keywords"] (list).
"""
from __future__ import annotations

import html
import re
from urllib.parse import urlencode, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import feed_items, to_iso

FEED = "https://www.jobbank.gc.ca/jobsearch/feed/jobSearchRSSfeed"
PAGE = 100


def _field(summary: str, label: str) -> str:
    m = re.search(rf"<strong>{label}:</strong>\s*(.*?)\s*(?:<br\s*/?>|$)", summary or "", re.I | re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


class JobBankCA(Provider):
    name = "jobbankca"
    wave = "W1"
    kind = "public"
    tenant = False
    hosts = ("www.jobbank.gc.ca",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        kws = list(target.options.get("keywords") or [])
        if not kws and target.query:
            kws = [k.strip() for k in target.query.split(",") if k.strip()]
        if not kws:
            raise ProviderError("jobbankca needs keywords (Target.query or options['keywords'])")
        max_pages = int(target.options.get("max_pages", 5))
        by_url: dict[str, Job] = {}
        errors = ok = 0
        for kw in kws:
            failed = False
            for page in range(1, max_pages + 1):
                try:
                    xml = ctx.http.get_text(f"{FEED}?{urlencode({'searchstring': kw, 'locationstring': '', 'page': page})}")
                    items = feed_items(xml)
                except Exception as e:  # first page failing marks the keyword failed
                    if page == 1:
                        failed = True
                        ctx.warn(f"jobbankca: {kw!r}: {e}")
                    break
                for it in items:
                    url = it.get("link", "")
                    p = urlsplit(url)
                    if p.scheme != "https" or p.netloc != "www.jobbank.gc.ca" or not it.get("title") or url in by_url:
                        continue
                    summ = it.get("description", "")
                    by_url[url] = self.job(
                        title=it["title"], url=url, company=_field(summ, "Employer"),
                        location=_field(summ, "Location"), country="CA",
                        posted_at=to_iso(it.get("published")), source_id=it.get("id", ""),
                    ).validate()
                if len(items) < PAGE or len(by_url) >= ctx.max_jobs:
                    break
            errors += failed
            ok += not failed
        if ok == 0 and errors:
            raise ProviderError(f"jobbankca: all {len(kws)} keyword request(s) failed")
        return list(by_url.values())[: ctx.max_jobs]


PROVIDER = JobBankCA()
