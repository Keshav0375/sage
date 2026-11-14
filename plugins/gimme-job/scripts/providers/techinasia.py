"""Tech in Asia jobs — Algolia index behind the site search, board-wide.

POST https://<appid>-dsn.algolia.net/1/indexes/*/queries  {"requests":[{"indexName":"job_postings","params":"query=&hitsPerPage=1000&page=N"}]}
The public search credentials are NOT hardcoded: pass options.algolia_app / options.algolia_key or set
GIMME_JOB_TECHINASIA_ALGOLIA_APP / GIMME_JOB_TECHINASIA_ALGOLIA_KEY.
Mechanism from career-ops providers/techinasia.mjs (MIT); code is our own.
"""
from __future__ import annotations

import json
import os
import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

SITE = "https://www.techinasia.com"
INDEX = "job_postings"
HITS_PER_PAGE = 1000
SHORTENERS = {"bit.ly", "cutt.ly", "goo.gl", "is.gd", "lnkd.in", "rb.gy", "rebrand.ly", "s.id",
              "shorturl.at", "t.co", "tinyurl.com"}


def _external(hit: dict) -> str:
    u = (hit.get("external_link") or "").strip() if isinstance(hit.get("external_link"), str) else ""
    p = urlsplit(u)
    if not u or p.scheme != "https" or p.netloc.lower() in SHORTENERS:
        return ""
    return u


def _company(raw) -> str:
    if isinstance(raw, str) and raw.strip():
        try:
            raw = json.loads(raw)
        except ValueError:
            return ""
    return (raw.get("name") or "").strip() if isinstance(raw, dict) else ""


class TechInAsia(Provider):
    name = "techinasia"
    wave = "W5"
    kind = "board"
    tenant = False
    hosts = ("www.techinasia.com", "algolia.net")

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = target.options
        app = str(o.get("algolia_app") or os.environ.get("GIMME_JOB_TECHINASIA_ALGOLIA_APP") or "").strip()
        key = str(o.get("algolia_key") or os.environ.get("GIMME_JOB_TECHINASIA_ALGOLIA_KEY") or "").strip()
        if not app or not key:
            raise ProviderError("techinasia needs GIMME_JOB_TECHINASIA_ALGOLIA_APP and GIMME_JOB_TECHINASIA_ALGOLIA_KEY "
                                "(or options.algolia_app / options.algolia_key)")
        if not re.fullmatch(r"[A-Za-z0-9]{6,16}", app):
            raise ProviderError("techinasia: unexpected Algolia app id")
        url = (f"https://{app.lower()}-dsn.algolia.net/1/indexes/*/queries?x-algolia-application-id={quote(app)}"
               f"&x-algolia-api-key={quote(key)}")
        query = quote((target.query or "").strip())
        max_pages = min(int(o.get("max_pages") or 5), 50)
        hits: list[dict] = []
        for page in range(max_pages):
            body = {"requests": [{"indexName": INDEX, "params": f"query={query}&hitsPerPage={HITS_PER_PAGE}&page={page}"}]}
            data = ctx.http.post_json(url, body, headers={"Referer": SITE + "/", "Content-Type": "application/x-www-form-urlencoded"})
            if not isinstance(data, dict) or "results" not in data:
                raise ProviderError("techinasia: unexpected Algolia response, no results")
            res = (data["results"] or [None])[0]
            if not res:
                break
            if not isinstance(res.get("hits"), list):
                raise ProviderError("techinasia: unexpected Algolia response, no results[0].hits")
            hits.extend(res["hits"])
            if not res["hits"] or page + 1 >= int(res.get("nbPages") or 1):
                break
        counts: dict[str, int] = {}
        for h in hits:
            e = _external(h)
            if e:
                counts[e] = counts.get(e, 0) + 1
        out: dict[str, Job] = {}
        for h in hits:
            title = (h.get("title") or "").strip() if isinstance(h.get("title"), str) else ""
            ext = _external(h)
            hid = str(h.get("id") or h.get("objectID") or "").strip()
            link = ext if ext and counts.get(ext, 0) <= 1 else (f"{SITE}/jobs/{quote(hid, safe='')}" if hid else "")
            if not title or not link or link in out:
                continue
            city = h.get("city") if isinstance(h.get("city"), dict) else {}
            parts: list[str] = []
            for k in ("name", "country_name"):
                v = (city.get(k) or "").strip() if isinstance(city.get(k), str) else ""
                if v and v not in parts:
                    parts.append(v)
            remote = bool(h.get("is_remote"))
            if remote:
                parts.append("Remote")
            pub = h.get("published_at") or ""
            if isinstance(pub, str) and re.fullmatch(r"\d{4}-\d\d-\d\d \d\d:\d\d:\d\d", pub.strip()):
                pub = pub.strip().replace(" ", "T") + "Z"
            out[link] = self.job(
                title=title, url=link, company=_company(h.get("company")) or "Tech in Asia",
                location=", ".join(parts), locations=parts, workplace="remote" if remote else "",
                description=html_to_text(h.get("description") or ""), posted_at=to_iso(pub), source_id=hid,
            ).validate()
            if len(out) >= ctx.max_jobs:
                break
        return list(out.values())


PROVIDER = TechInAsia()
