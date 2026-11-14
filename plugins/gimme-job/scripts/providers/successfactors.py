"""SAP SuccessFactors career sites — RMK tile search (HTML), falling back to the CSB jobs API.

Mechanism from career-ops providers/successfactors.mjs (MIT); main path only (default locales, no sweeps).
"""
from __future__ import annotations

import html
import re
from datetime import date
from urllib.parse import urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

MAX_PAGES = 40
CSB_PAGE_SIZE = 10
CSB_MAX_PAGES = 100
LOCALE_PRIORITY = ["de_DE", "en_US", "en_GB", "en_EN"]
MONTH_FIRST = {"en_US", "es_US"}


def _clean(s: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]*>", " ", s or "")).split())


def _config(url: str):
    p = urlsplit(url or "")
    host = p.netloc.lower()
    if p.scheme != "https" or "." not in host or p.username or p.port:
        return None
    path = re.sub(r"/go/[^/]+/\d+(?:/\d+)?/?$", "", p.path, flags=re.I)
    path = re.sub(r"/(?:search|tile-search-results|services/recruiting/v1/jobs)/?$", "", path, flags=re.I).rstrip("/")
    origin = f"https://{p.netloc}"
    base = origin + path
    return {"origin": origin, "base": base}


def parse_tiles(page: str, origin: str) -> list[dict]:
    out = []
    for m in re.finditer(r'<li class="job-tile job-id-(\d+)\b.*?</li>', page, re.S):
        block = m.group(0)
        u = re.search(r'data-url="([^"]+)"', block)
        t = re.search(r'class="jobTitle-link[^"]*"[^>]*>(.*?)</a>', block, re.S)
        if not u or not t or not _clean(t.group(1)):
            continue
        path = html.unescape(u.group(1))
        city = re.search(r'id="[^"]*-section-city-value">(.*?)</div>', block, re.S)
        url = path if re.match(r"https?://", path, re.I) else origin + (path if path.startswith("/") else "/" + path)
        out.append({"id": m.group(1), "title": _clean(t.group(1)), "url": url,
                    "location": _clean(city.group(1)) if city else ""})
    return out


def parse_csb_date(raw, locale: str) -> str:
    s = str(raw or "").strip()
    try:
        m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", s)
        if m:
            a, b, y = (int(x) for x in m.groups())
            mo, d = (a, b) if locale in MONTH_FIRST else (b, a)
        elif (m := re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", s)):
            d, mo, y = (int(x) for x in m.groups())
        elif (m := re.fullmatch(r"(\d{4})[.\-/]\s*(\d{1,2})[.\-/]\s*(\d{1,2})\.?", s)):
            y, mo, d = (int(x) for x in m.groups())
        else:
            return ""
        return date(y + 2000 if y < 100 else y, mo, d).isoformat()
    except ValueError:
        return ""


class SuccessFactors(Provider):
    name = "successfactors"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("successfactors.eu", "successfactors.com", "jobs2web.com")

    def detect(self, careers_url: str):
        if re.search(r"successfactors\.(eu|com)|jobs2web\.com", careers_url or "", re.I) and _config(careers_url):
            return Target(careers_url=careers_url, api_url=careers_url,
                          slug=urlsplit(careers_url).netloc.split(".")[0])
        return None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        cfg = _config(target.api_url or target.careers_url)
        if not cfg:
            raise ProviderError("successfactors needs an https careers url")
        company = target.company or urlsplit(cfg["origin"]).netloc.split(".")[0]
        if str(target.options.get("variant", "")).lower() != "csb":
            jobs = self._rmk(cfg, company, ctx)
            if jobs:
                return jobs
        return self._csb(cfg, company, ctx)

    def _rmk(self, cfg, company, ctx) -> list[Job]:
        jobs: list[Job] = []
        seen: set[str] = set()
        start = 0
        for _ in range(MAX_PAGES):
            page = ctx.http.get_text(f"{cfg['base']}/tile-search-results/?startrow={start}", headers={"Accept": "text/html"})
            raw = re.findall(r'<li class="job-tile job-id-(\d+)', page)
            if not raw or all(i in seen for i in raw):
                break
            for t in parse_tiles(page, cfg["origin"]):
                if t["id"] in seen:
                    continue
                jobs.append(self.job(title=t["title"], url=t["url"], company=company, location=t["location"],
                                     source_id=t["id"]).validate())
            seen.update(raw)
            if len(jobs) >= ctx.max_jobs:
                return jobs[: ctx.max_jobs]
            start += len(raw)
        return jobs

    def _csb(self, cfg, company, ctx) -> list[Job]:
        locales = ["de_DE", "en_US"]
        try:
            found = set(re.findall(r"locale=([a-z]{2}_[A-Z]{2})\b", ctx.http.get_text(cfg["base"] + "/search/")))
            if found:
                locales = sorted(found, key=lambda x: (LOCALE_PRIORITY.index(x) if x in LOCALE_PRIORITY else 99, x))[:16]
        except ProviderError:
            pass
        api = cfg["base"] + "/services/recruiting/v1/jobs"
        jobs: list[Job] = []
        seen: set[str] = set()
        first_err = None
        for loc in locales:
            try:
                for page in range(CSB_MAX_PAGES):
                    data = ctx.http.post_json(api, {"keywords": "", "locale": loc, "location": "", "pageNumber": page, "sortBy": "date"})
                    items = (data or {}).get("jobSearchResult") or []
                    if not items:
                        break
                    for it in items:
                        r = (it or {}).get("response") or {}
                        jid = str(r.get("id") or "")
                        title = _clean(str(r.get("unifiedStandardTitle") or r.get("jobTitle") or ""))
                        if not jid or not title or jid in seen:
                            continue
                        seen.add(jid)
                        slug = re.sub(r"-{2,}", "-", re.sub(r"[?#&]+", "-", html.unescape(str(r.get("unifiedUrlTitle") or r.get("urlTitle") or "job"))))
                        locs = r.get("jobLocationShort")
                        locs = locs if isinstance(locs, list) else ([locs] if locs else [])
                        places = list(dict.fromkeys(x for x in (_clean(str(p)).rstrip(", ") for p in locs) if x))
                        jobs.append(self.job(title=title, url=f"{cfg['base']}/job/{slug}/{jid}-{loc}", company=company,
                                             locations=places, location=" / ".join(places),
                                             posted_at=parse_csb_date(r.get("unifiedStandardStart"), loc),
                                             source_id=jid).validate())
                        if len(jobs) >= ctx.max_jobs:
                            return jobs
                    total = (data or {}).get("totalJobs")
                    if len(items) < CSB_PAGE_SIZE or (isinstance(total, int) and (page + 1) * CSB_PAGE_SIZE >= total):
                        break
            except ProviderError as e:
                first_err = first_err or e
        if not jobs and first_err:
            raise first_err
        return jobs


PROVIDER = SuccessFactors()
