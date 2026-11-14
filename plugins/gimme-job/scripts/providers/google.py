"""Google Careers — server-rendered results pages (no auth).

GET https://www.google.com/about/careers/applications/jobs/results/?q=..&location=..&sort_by=date[&page=N]
Cards are anchors to jobs/results/{id}-{slug} with an h3 title and a "<employer> | <loc>; <loc>" line.
Queries: target.query, else options['queries'], else a small default list. Location: target.location or options.
Mechanism from career-ops providers/google.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import urlencode

from ._base import Context, Job, Provider, Target
from ._parse import html_to_text

BASE = "https://www.google.com/about/careers/applications/jobs/results/"
PAGE_SIZE = 20
ANCHOR = re.compile(r'<a\b[^>]*?\bhref="(?:[^"]*/)?jobs/results/(\d+)-([a-z0-9-]+)[^"]*"[^>]*>')
H3 = re.compile(r"<h3\b[^>]*>([^<]+)</h3>")
EMPLOYER = re.compile(r'<p class="l103df">(.*?)</p>', re.S)
ARIA = re.compile(r'\baria-label="Learn more about ([^"]+)"')
MORE = re.compile(r"^\+\d+ more$")
DEFAULT_QUERIES = ["business strategy", "business operations", "strategy and operations",
                   "corporate development", "financial planning"]


def parse_results_page(html: str):
    cards, prev = [], 0
    for a in ANCHOR.finditer(html or ""):
        card = html[prev:a.start()]
        prev = a.end()
        slug = a.group(2)
        h3 = H3.findall(card)
        aria = ARIA.search(a.group(0))
        title = (html_to_text(h3[-1]) if h3 else "") or (html_to_text(aria.group(1)) if aria else "") \
            or slug.replace("-", " ").title()
        lines = EMPLOYER.findall(card)
        employer, locs = "", []
        if lines and "|" in lines[-1]:
            emp, _, rest = lines[-1].partition("|")
            employer = html_to_text(emp)
            locs = [l.strip() for l in html_to_text(rest).split(";") if l.strip() and not MORE.match(l.strip())]
        cards.append({"id": a.group(1), "slug": slug, "title": title, "employer": employer, "locations": locs})
    return cards


class Google(Provider):
    name = "google"
    wave = "W3"
    kind = "company"
    tenant = False
    hosts = ("google.com",)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = target.options
        queries = [target.query] if target.query else (o.get("queries") or DEFAULT_QUERIES)
        location = target.location or o.get("location") or "United States"
        max_pages = min(int(o.get("max_pages") or 10), 50)
        by_id: dict[str, Job] = {}
        for q in queries:
            seen: set[str] = set()
            for page in range(1, max_pages + 1):
                params = {"q": q, "location": location, "sort_by": "date"}
                if page > 1:
                    params["page"] = page
                cards = parse_results_page(ctx.http.get_text(f"{BASE}?{urlencode(params)}"))
                new = 0
                for c in cards:
                    if c["id"] not in seen:
                        seen.add(c["id"])
                        new += 1
                    if c["id"] in by_id:
                        continue
                    by_id[c["id"]] = self.job(
                        title=c["title"], url=f"{BASE}{c['id']}-{c['slug']}",
                        company=c["employer"] or "Google", location="; ".join(c["locations"]),
                        locations=c["locations"], source_id=c["id"],
                    ).validate()
                    if len(by_id) >= ctx.max_jobs:
                        return list(by_id.values())
                if not cards or not new or len(cards) < PAGE_SIZE:
                    break
        return list(by_id.values())


PROVIDER = Google()
