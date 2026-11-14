"""TalentLink (Lumesse / Cornerstone) — career page → FO host + site id, then FO REST /fo/rest/jobs.

Mechanism from career-ops providers/talentlink.mjs (MIT); code is our own.
Simplified: location comes from the location-type SLOVLIST fields only (no bindTo expansion).
"""
from __future__ import annotations

import html as htmllib
import re
from urllib.parse import quote, urlsplit, urljoin

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

PAGE_SIZE = 100
MAX_PAGES = 20
VENDOR_HOST = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.recruitmentplatform\.com$")
FO_HOST = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:recruitmentplatform|lumessetalentlink|sabatalentlink)\.com$")
SITE_ID = re.compile(r"^[A-Z0-9]{10,40}$")
SEG = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
PAGE_FILE = re.compile(r"^[A-Za-z0-9_-]{1,64}\.html?$")
LOC_LIST = re.compile(r"locat|countr|city|county|region|destination|based at|office|standort|\bland\b|\bort\b|pays|ville|lieu|sede|ubicaci|pa[ií]s|ciudad|citt[aà]|miasto|lokalizac", re.I)


def _board(url: str, vendor_only: bool = True):
    p = urlsplit((url or "").strip())
    host = (p.hostname or "").lower()
    if p.scheme != "https" or (vendor_only and not VENDOR_HOST.match(host)) or not host:
        return None
    segs = [s for s in p.path.split("/") if s]
    f = segs.pop() if segs and not p.path.endswith("/") and "." in segs[-1] else "index.html"
    if not PAGE_FILE.match(f) or not all(SEG.match(s) for s in segs):
        return None
    d = f"https://{host}/" + "".join(s + "/" for s in segs)
    return d + f, d


def _clean(v) -> str:
    return re.sub(r"\s+", " ", htmllib.unescape(v)).strip() if isinstance(v, str) else ""


def _headers(site: str) -> dict:
    return {"Accept": "application/json", "username": f"{site}:guest:FO", "password": "guest"}


class TalentLink(Provider):
    name = "talentlink"
    wave = "W4"
    kind = "ats"
    tenant = True
    hosts = ("recruitmentplatform.com", "lumessetalentlink.com", "sabatalentlink.com")

    def detect(self, careers_url: str):
        b = _board(careers_url)
        return Target(careers_url=careers_url, api_url=b[0]) if b else None

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        raw = next((u for u in (target.api_url, target.careers_url) if u and _board(u, vendor_only=False)), "")
        board = _board(raw, vendor_only=False) if raw else None
        if not board:
            raise ProviderError("talentlink needs the https career page URL")
        page_url, board_dir = board
        html = ctx.http.get_text(page_url)
        hm = re.search(r'data-(?:lumesse|talentlink)-fo-host="([^"]*)"', html)
        sm = re.search(r'data-(?:lumesse-site|talentlink-fo-site)-tech-id="([^"]*)"', html)
        if not hm or not sm:
            raise ProviderError("talentlink: no FO widget on the page (or syndicated job list, unsupported)")
        fo = re.sub(r"^https://|/$", "", hm.group(1).strip().lower())
        site = sm.group(1).strip()
        if not FO_HOST.match(fo) or not SITE_ID.match(site):
            raise ProviderError("talentlink: FO host or site id has an unexpected format")
        api = f"https://{fo}/fo/rest"
        hdr = _headers(site)
        detail = board_dir + "details.html"
        try:
            cfg = ctx.http.get_json(f"{api}/config", headers=hdr)
            conf = ((cfg or {}).get("navigationPages") or {}).get("jobDescriptionURL")
            if isinstance(conf, str) and conf.strip():
                u = urlsplit(urljoin(board_dir, conf.strip()))
                last = u.path.rsplit("/", 1)[-1]
                if u.scheme == "https" and u.hostname == urlsplit(page_url).hostname and PAGE_FILE.match(last):
                    detail = f"https://{u.hostname}{u.path}"
        except Exception:
            pass
        loc_fields: set[str] = set()
        try:
            crit = ctx.http.get_json(f"{api}/jobs/criteria", headers=hdr)
            for key, lst in (crit or {}).items():
                m = re.match(r"^LOV(\d+)$", key)
                if m and isinstance(lst, dict) and isinstance(lst.get("lovName"), str) and LOC_LIST.search(lst["lovName"]):
                    loc_fields.add(f"SLOVLIST{m.group(1)}")
        except Exception:
            pass
        company = target.company or fo.split(".")[0]
        jobs: list[Job] = []
        seen: set[str] = set()
        for page in range(MAX_PAGES):
            data = ctx.http.post_json(
                f"{api}/jobs?firstResult={page * PAGE_SIZE}&maxResults={PAGE_SIZE}&sortBy=DPOSTINGSTART&sortOrder=desc",
                {"searchCriteria": {}}, headers=hdr)
            rows = (data or {}).get("jobs") if isinstance(data, dict) else None
            if rows is None and isinstance(data, dict) and (data.get("globals") or {}).get("jobsCount") == 0:
                rows = []
            if not isinstance(rows, list):
                raise ProviderError("talentlink: unexpected response, expected jobs[]")
            for r in rows:
                if not isinstance(r, dict):
                    continue
                f = r.get("jobFields") if isinstance(r.get("jobFields"), dict) else {}
                jid = r.get("id", f.get("id"))
                if not (isinstance(jid, int) or (isinstance(jid, str) and jid.isdigit())):
                    continue
                title = _clean(f.get("jobTitle"))
                if not title:
                    continue
                url = f"{detail}?jobId={quote(str(jid), safe='')}"
                if url in seen:
                    continue
                seen.add(url)
                places: list[str] = []
                for k in f:
                    if k in loc_fields:
                        v = _clean(f[k])
                        if v and v not in places:
                            places.append(v)
                modes = [_clean(m).lower() for m in f.get("WorkMode") or []] if isinstance(f.get("WorkMode"), list) else []
                loc = ", ".join(places)
                workplace = "remote" if "remote" in modes else "hybrid" if "hybrid" in modes else ""
                parts = []
                for c in r.get("customFields") or []:
                    if isinstance(c, dict):
                        body = html_to_text(c.get("content") or "")
                        if body:
                            t = _clean(c.get("title"))
                            parts.append(f"{t}: {body}" if t else body)
                jobs.append(self.job(
                    title=title, url=url, company=company, location=loc, workplace=workplace,
                    posted_at=to_iso(f.get("DPOSTINGSTART")), description=" ".join(parts),
                    source_id=str(jid),
                ).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            if len(rows) < PAGE_SIZE:
                break
        return jobs


PROVIDER = TalentLink()
