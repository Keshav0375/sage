"""Hacker News "Ask HN: Who is hiring?" — Algolia HN API (no auth).

GET https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring&hitsPerPage=5
GET https://hn.algolia.com/api/v1/items/{thread_id}   (top-level comments = postings)
Mechanism from career-ops providers/hackernews.mjs (MIT); code is our own.
"""
from __future__ import annotations

import html
import re
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import to_iso

SEARCH = "https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring&hitsPerPage=5"
URL_RE = re.compile(r"https?://[^\s<>\"')]+")
THREAD_RE = re.compile(r"ask\s+hn[:\s]+who\s+is\s+hiring", re.I)
JOBS_PATH = re.compile(r"/(?:careers?|jobs)(?:/|$)", re.I)
ATS_HOSTS = ("greenhouse.io", "lever.co", "ashbyhq.com", "workable.com", "recruitee.com", "bamboohr.com",
             "smartrecruiters.com", "myworkdayjobs.com", "teamtailor.com", "personio.de", "personio.com",
             "workatastartup.com", "jobs.gem.com")
PLACEHOLDER = re.compile(r"^[\[<({]?\s*(?:company(?:\s+name)?|name)\s*[\]>)}]?$", re.I)


def _urls(text: str) -> list[str]:
    return [u.rstrip(".,;!?)") for u in URL_RE.findall(text)]


def _job_like(u: str) -> bool:
    p = urlsplit(u)
    h = p.netloc.lower()
    return any(h == a or h.endswith("." + a) for a in ATS_HOSTS) or bool(JOBS_PATH.search(p.path))


def parse_comment(text: str, fallback_url: str = "") -> dict | None:
    if not text:
        return None
    t = re.sub(r'<a\s[^>]*href="([^"]+)"[^>]*>.*?</a>', r"\1", text, flags=re.I | re.S)
    t = re.sub(r"</?(?:p|br|div|li|h[1-6])\b[^>]*>", "\n", t, flags=re.I)
    plain = html.unescape(re.sub(r"<[^>]+>", " ", t))
    lines = [l.strip() for l in plain.splitlines() if l.strip()]
    if not lines:
        return None
    first = lines[0]
    parts = [p.strip() for p in first.split("|")]
    company = location = ""
    if len(parts) >= 3:
        company = re.sub(r"\s{2,}", " ", re.sub(r"\(\s*\)|\[\s*\]", "", URL_RE.sub("", parts[0]))).strip()
        location = URL_RE.sub("", parts[2]).strip()
    elif len(parts) == 2:
        company = re.sub(r"\s{2,}", " ", URL_RE.sub("", parts[0])).strip()
    if PLACEHOLDER.match(company):
        company = ""
    title = re.sub(r"\s{2,}", " ", URL_RE.sub("", first)).strip()
    if not title:
        return None
    urls = (_urls(" ".join(parts[3:])) or [u for u in _urls(plain) if _job_like(u)] or [fallback_url])
    url = urls[0]
    if not url:
        return None
    return {"title": title, "url": url, "company": company, "location": location, "description": "\n".join(lines[1:])}


class HackerNews(Provider):
    name = "hackernews"
    wave = "W1"
    kind = "board"
    tenant = False
    hosts = ("hn.algolia.com", "news.ycombinator.com")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        data = ctx.http.get_json(SEARCH)
        tid = next((h["objectID"] for h in (data or {}).get("hits", [])
                    if isinstance(h.get("objectID"), str) and THREAD_RE.search(h.get("title", ""))), None)
        if not tid:
            raise ProviderError('hackernews: no "Ask HN: Who is hiring?" thread found')
        item = ctx.http.get_json(f"https://hn.algolia.com/api/v1/items/{tid}")
        if not isinstance(item, dict):
            raise ProviderError("hackernews: bad item response")
        words = [w.lower() for w in (target.query or "").split()]
        jobs: list[Job] = []
        for c in item.get("children") or []:
            if not c or c.get("deleted") or c.get("dead") or not (c.get("text") or "").strip():
                continue
            cid = c.get("id") or c.get("objectID")
            fb = f"https://news.ycombinator.com/item?id={cid}" if cid is not None else f"https://news.ycombinator.com/item?id={tid}"
            p = parse_comment(c["text"], fb)
            if not p:
                continue
            if words and not any(w in (p["title"] + " " + p["description"]).lower() for w in words):
                continue
            jobs.append(self.job(
                title=p["title"], url=p["url"], company=p["company"], location=p["location"],
                workplace="remote" if re.search(r"\bremote\b", p["location"], re.I) else "",
                posted_at=to_iso(c.get("created_at")), description=p["description"],
                source_id=str(cid or ""), extra={"thread_id": tid},
            ).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        return jobs


PROVIDER = HackerNews()
