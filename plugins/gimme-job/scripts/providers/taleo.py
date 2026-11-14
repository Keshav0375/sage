"""Taleo (TEE career sections) — portal id from the shell page, then POST the searchjobs REST endpoint.

Mechanism from career-ops providers/taleo.mjs (MIT); main path only (no detail fetch).
"""
from __future__ import annotations

import html
import json
import re
from urllib.parse import quote, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target
from ._parse import html_to_text, to_iso

HOST_RE = re.compile(r"^[a-z0-9-]+\.taleo\.net$", re.I)
SECTION_RE = re.compile(r"^/careersection/([a-z0-9._-]+)/(?:jobsearch|joblist|jobdetail)\.ftl$", re.I)
MAX_PAGES = 100
HEADERS = {"X-Requested-With": "XMLHttpRequest", "Accept": "application/json, text/javascript, */*; q=0.01"}


def _board(url: str):
    p = urlsplit(url or "")
    host = p.netloc.lower()
    if p.scheme != "https" or host == "tre.taleo.net" or not HOST_RE.match(host):
        return None
    m = SECTION_RE.match(p.path)
    return (host, m.group(1)) if m else None


def _text(v) -> str:
    if v is None:
        return ""
    if isinstance(v, (str, int, float)):
        return html_to_text(str(v))
    if isinstance(v, list):
        return ", ".join(x for x in (_text(i) for i in v) if x)
    if isinstance(v, dict):
        for k in ("value", "text", "label", "name", "displayValue"):
            if v.get(k) is not None:
                return _text(v[k])
    return ""


def _location(v: str) -> str:
    s = (v or "").strip()
    if s.startswith("["):
        try:
            arr = json.loads(s)
            if isinstance(arr, list) and all(isinstance(x, str) for x in arr):
                return "; ".join(x for x in (html_to_text(a) for a in arr) if x)
        except ValueError:
            pass
    return s


def _headings(shell: str) -> list[str]:
    m = re.search(r'<table\b[^>]*id=["\']jobs["\'][^>]*>.*?<thead\b[^>]*>(.*?)</thead>', shell, re.S | re.I)
    src = m.group(1) if m else shell
    out = []
    for h in re.findall(r"<(?:th|label)[^>]*>(.*?)</(?:th|label)>", src, re.S | re.I):
        v = html_to_text(h)
        if v and not re.fullmatch(r"(?i)icons?|actions?", v):
            out.append(v)
    return out


def _idx(labels, pats):
    for i, h in enumerate(labels):
        if any(re.search(p, h, re.I) for p in pats):
            return i
    return -1


class Taleo(Provider):
    name = "taleo"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ("taleo.net",)

    def detect(self, careers_url: str):
        b = _board(careers_url)
        if not b:
            return None
        return Target(slug=b[1], careers_url=careers_url, api_url=careers_url)

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        b = _board(target.api_url) or _board(target.careers_url)
        if not b:
            raise ProviderError("taleo needs an https *.taleo.net careersection url")
        host, section = b
        shell_url = target.api_url or target.careers_url
        shell = ctx.http.get_text(shell_url)
        pm = (re.search(r"[?&]portal=(\d+)", shell, re.I) or re.search(r"[\"']portal(?:Id)?[\"']?\s*[:=]\s*[\"']?(\d+)", shell, re.I)
              or re.search(r"name=[\"']portal[\"'][^>]*value=[\"'](\d+)", shell, re.I))
        if not pm:
            raise ProviderError("taleo: career section has no public portal id")
        lm = re.search(r"[?&]lang=([\w-]+)", shell_url)
        lang = lm.group(1) if lm else "en"
        headings = _headings(shell)
        api = f"https://{host}/careersection/rest/jobboard/searchjobs?lang={lang}&portal={pm.group(1)}"
        ti = _idx(headings, [r"requisition\s*title", r"job\s*title", r"^title$"])
        li = _idx(headings, [r"location", r"city"])
        di = _idx(headings, [r"posting\s*date", r"date\s*posted", r"posted"])
        positional = not headings
        jobs: list[Job] = []
        for page in range(1, MAX_PAGES + 1):
            body = {"multilineEnabled": False,
                    "sortingSelection": {"sortBySelectionParam": "5", "ascendingSortingOrder": "true"},
                    "fieldData": {"fields": {"KEYWORD": "", "LOCATION": ""}, "valid": True},
                    "filterSelectionParam": {"searchFilterSelections": []},
                    "advancedSearchFiltersSelectionParam": {"searchFilterSelections": []},
                    "pageNo": page}
            data = ctx.http.post_json(api, body, headers=HEADERS)
            rows = (data or {}).get("requisitionList")
            if not isinstance(rows, list):
                if not data:
                    break
                raise ProviderError("taleo: unexpected response, no requisitionList")
            for r in rows:
                rid = str(r.get("contestNo") or r.get("jobId") or "").strip()
                cols = [_text(c) for c in (r.get("column") or [])]
                get = lambda i, d: cols[i] if 0 <= i < len(cols) else (cols[d] if positional and d < len(cols) else "")
                title = get(ti, 0)
                if not rid or not title:
                    continue
                jobs.append(self.job(
                    title=title,
                    url=f"https://{host}/careersection/{quote(section)}/jobdetail.ftl?job={quote(rid)}&lang={lang}",
                    company=target.company or host.split(".")[0],
                    location=_location(get(li, 1)),
                    posted_at=to_iso(get(di, 2)),
                    source_id=rid).validate())
                if len(jobs) >= ctx.max_jobs:
                    return jobs
            try:
                total = int(((data or {}).get("pagingData") or {}).get("totalCount"))
            except (TypeError, ValueError):
                total = None
            if not rows or (total is not None and len(jobs) >= total):
                break
        return jobs


PROVIDER = Taleo()
