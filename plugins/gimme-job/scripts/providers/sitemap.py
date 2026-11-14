"""Generic sitemap.xml careers source — jobs derived from URLs that match a configured pattern.

Config (all in ``Target.options``; sitemap URL from options['url'] / api_url / careers_url):
  job_path        regex on the URL path with a named group ``slug`` (``(?<slug>..)`` is accepted too);
                  optional groups ``posting_id`` / ``req_id``
  index_filter    regex a child-sitemap URL must match (for <sitemapindex>)
  max_sitemaps    child sitemaps to read (default 50)
  fetchDetails    true: enrich the first ``detailLimit`` (default 25) rows from JSON-LD JobPosting on the detail page
The title comes from the slug; company from Target.company. Same-host URLs only. Gzipped sitemaps unsupported.
Mechanism from career-ops providers/sitemap.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from urllib.parse import unquote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, json_ld_jobs, to_iso

ACRONYMS = {w.lower(): w for w in ("AI", "ML", "QA", "UX", "UI", "IT", "HR", "SRE", "SDET", "API", "iOS", "DevOps", "SaaS", "CTO", "CEO", "CFO", "VP", "II", "III", "IV")}
MAX_URLS = 50_000


def title_from_slug(slug: str) -> str:
    dec = unquote(slug)
    parts = []
    for seg in re.split(r"--+", dec):
        words = re.sub(r"[-_]+", " ", seg).split()
        seg_t = " ".join(ACRONYMS.get(w.lower()) or (w[0].upper() + w[1:]) for w in words if w)
        if seg_t:
            parts.append(seg_t)
    return " - ".join(parts)


def _site(raw: str):
    p = urlsplit((raw or "").strip())
    host = (p.hostname or "").lower().rstrip(".")
    if p.scheme != "https" or p.username or p.port or "." not in host or re.fullmatch(r"[\d.]+", host) \
            or host.endswith((".local", ".internal")) or host.startswith("localhost"):
        return None
    return p, host


def _locs(xml: str):
    xml = re.sub(r"<!--.*?-->", "", xml, flags=re.S)

    def loc(block: str) -> str:
        m = re.search(r"<loc\b[^>]*>(.*?)</loc\s*>", block, re.S | re.I)
        if not m:
            return ""
        import html as _h
        return _h.unescape(re.sub(r"^\s*<!\[CDATA\[(.*?)\]\]>\s*$", r"\1", m.group(1), flags=re.S).strip())

    if re.search(r"<sitemapindex\b", xml, re.I):
        if not re.search(r"</sitemapindex\s*>", xml, re.I):
            raise ProviderError("sitemap: truncated response (<sitemapindex>)")
        return "index", [l for l in (loc(m) for m in re.findall(r"<sitemap\b[^>]*>(.*?)</sitemap\s*>", xml, re.S | re.I)) if l]
    if re.search(r"<urlset\b", xml, re.I):
        if not re.search(r"</urlset\s*>|<urlset\b[^>]*/>", xml, re.I):
            raise ProviderError("sitemap: truncated response (<urlset>)")
        return "urlset", [l for l in (loc(m) for m in re.findall(r"<url\b[^>]*>(.*?)</url\s*>", xml, re.S | re.I)) if l]
    raise ProviderError("sitemap: expected an XML <urlset> or <sitemapindex>")


def _address(a) -> str:
    if not isinstance(a, dict):
        return ""
    c = a.get("addressCountry")
    c = c.get("name") if isinstance(c, dict) else c
    return ", ".join(dict.fromkeys(str(x).strip() for x in (a.get("addressLocality"), a.get("addressRegion"), c) if x and str(x).strip()))


class Sitemap(Provider):
    name = "sitemap"
    wave = "W3"
    kind = "feed"
    tenant = True
    hosts = ()

    def detect(self, careers_url: str):
        return None  # needs explicit job_path config

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        o = target.options
        site = _site(o.get("url") or target.api_url or target.careers_url)
        if not site:
            raise ProviderError("sitemap needs a public https sitemap URL")
        sp, host = site
        sm_url = f"https://{host}{sp.path}" + (f"?{sp.query}" if sp.query else "")
        if sp.path.lower().endswith(".gz"):
            raise ProviderError("sitemap: gzipped sitemaps are not supported")
        pat = str(o.get("job_path") or "").strip()
        if not pat:
            raise ProviderError("sitemap: options.job_path is required")
        pat = pat.replace("(?<slug>", "(?P<slug>").replace("(?<posting_id>", "(?P<posting_id>").replace("(?<req_id>", "(?P<req_id>")
        try:
            job_path = re.compile(pat)
        except re.error as e:
            raise ProviderError(f"sitemap: job_path is not a valid regex ({e})") from e
        if "slug" not in job_path.groupindex:
            raise ProviderError("sitemap: job_path must declare a (?P<slug>...) group")
        idx_filter = re.compile(str(o["index_filter"])) if o.get("index_filter") else None

        def same_site(u: str):
            p = urlsplit(u)
            ok = p.scheme == "https" and not p.username and not p.port and (p.hostname or "").lower().rstrip(".") == host
            return p if ok else None

        kind, locs = _locs(ctx.http.get_text(sm_url))
        if kind == "index":
            children = [c for c in locs if same_site(c) and not urlsplit(c).path.lower().endswith(".gz")
                        and (not idx_filter or idx_filter.search(c))]
            if not locs:
                raise ProviderError("sitemap: the sitemap index lists no child sitemaps")
            urls: list[str] = []
            readable = 0
            for c in children[: int(o.get("max_sitemaps") or 50)]:
                try:
                    k, sub = _locs(ctx.http.get_text(c))
                except ProviderError as e:
                    ctx.warn(f"sitemap: child {c} failed ({e})")
                    continue
                if k == "index":
                    continue
                urls += sub[:MAX_URLS]
                readable += 1
            if readable == 0:
                raise ProviderError("sitemap: no usable child sitemaps")
            locs = urls
        locs = locs[:MAX_URLS]

        jobs: list[Job] = []
        seen: set[str] = set()
        for loc in locs:
            p = same_site(loc)
            if not p:
                continue
            m = job_path.search(p.path)
            slug = m.group("slug") if m else ""
            title = title_from_slug(slug) if slug else ""
            if not title:
                continue
            pid = (m.groupdict().get("posting_id") or "").strip()
            href = loc.split("#")[0]
            key = pid or href
            if key in seen:
                continue
            seen.add(key)
            jobs.append(self.job(title=title, url=href, company=target.company, source_id=pid,
                                 extra={"requisition_id": m.groupdict()["req_id"]} if m.groupdict().get("req_id") else {}).validate())
            if len(jobs) >= ctx.max_jobs:
                break
        if locs and not jobs:
            raise ProviderError(f"sitemap: {len(locs)} URLs but none matched job_path")

        if o.get("fetchDetails") is True:
            limit = min(int(o.get("detailLimit") or 25), 200)
            for job in jobs[:limit]:
                try:
                    postings = json_ld_jobs(ctx.http.get_text(job.url))
                except ProviderError:
                    continue
                if not postings:
                    continue
                d = postings[0]
                locs_ = d.get("jobLocation")
                locs_ = locs_ if isinstance(locs_, list) else [locs_]
                loc_s = "; ".join(x for x in (_address((l or {}).get("address")) for l in locs_ if isinstance(l, dict)) if x)
                if isinstance(d.get("title"), str) and d["title"].strip():
                    job.title = d["title"].strip()
                if loc_s:
                    job.location = loc_s
                desc = html_to_text(d.get("description") or "")
                if desc:
                    job.description = desc
                job.posted_at = to_iso(d.get("datePosted")) or job.posted_at
        return jobs


PROVIDER = Sitemap()
