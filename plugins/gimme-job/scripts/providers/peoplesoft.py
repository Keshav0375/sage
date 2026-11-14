"""PeopleSoft Candidate Gateway (HRS_HRAM_FL) — anonymous search page scrape with "load more" form posts.

Mechanism from career-ops providers/peoplesoft.mjs (MIT); main path only (no detail pages). The session cookie
is carried best-effort from the ``set-cookie`` header the HTTP layer exposes.
"""
from __future__ import annotations

import html
import re
from datetime import datetime
from urllib.parse import quote, urlencode, urljoin, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

PATH_RE = re.compile(r"^/psc/([^/]+)/EMPLOYEE/HRMS/c/HRS_HRAM_FL\.HRS_CG_SEARCH_FL\.GBL$", re.I)
LOAD_MORE = "HRS_AGNT_RSLT_I$hdown$0"
MAX_LOAD_MORE = 20
BROWSER = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
           "Accept-Language": "en-US,en;q=0.9"}


def _cfg(url: str):
    u = urlsplit(url or "")
    m = PATH_RE.match(u.path)
    if u.scheme != "https" or not m:
        return None
    return {"origin": f"https://{u.netloc}", "site": m.group(1)}


def _base(c) -> str:
    return f"{c['origin']}/psc/{c['site']}/EMPLOYEE/HRMS/c/HRS_HRAM_FL.HRS_CG_SEARCH_FL.GBL"


def _search_url(c) -> str:
    return _base(c) + "?Page=HRS_APP_SCHJOB_FL&Action=U&FOCUS=Applicant&SiteId=1"


def _detail_url(c, job_id: str) -> str:
    return _base(c) + f"?Page=HRS_APP_JBPST_FL&Action=U&FOCUS=Applicant&JobOpeningId={quote(job_id)}&PostingSeq=1&SiteId=1"


def extract_by_id(page: str, el_id: str):
    m = re.search(rf"""\bid=(?:"{re.escape(el_id)}"|'{re.escape(el_id)}'|{re.escape(el_id)}(?=[\s>]))""", page)
    if not m:
        return None
    tag_start = page.rfind("<", 0, m.start())
    open_end = page.find(">", m.start())
    nm = re.match(r"<([a-zA-Z][a-zA-Z0-9]*)", page[tag_start: tag_start + 40]) if tag_start >= 0 else None
    if open_end < 0 or not nm:
        return None
    if page[open_end - 1] == "/":
        return ""
    tag, depth = nm.group(1), 1
    for t in re.finditer(rf"<{tag}\b[^>]*>|</{tag}\s*>", page[open_end + 1:], re.I):
        depth += -1 if t.group(0)[1] == "/" else 1
        if depth == 0:
            return page[open_end + 1: open_end + 1 + t.start()]
    return None


def text_by_id(page: str, el_id: str):
    raw = extract_by_id(page, el_id)
    return None if raw is None else " ".join(html.unescape(re.sub(r"<[^>]*>", " ", raw)).split())


def _date(raw) -> str:
    try:
        return datetime.strptime((raw or "").strip(), "%m/%d/%Y").date().isoformat()
    except ValueError:
        return ""


def parse_search(page: str) -> dict:
    form = re.search(r"""<form\b[^>]*\bname=["']win0["'][^>]*>""", page, re.I)
    if not form:
        return {"valid": False, "rows": [], "total": None, "action": None, "fields": {}}
    end = page.lower().find("</form>", form.start())
    body = page[form.start(): end if end >= 0 else len(page)]
    act = re.search(r"""\baction=["']([^"']*)["']""", form.group(0), re.I)
    fields = {}
    for im in re.finditer(r"<input\b([^>]*)>", body, re.I):
        a = dict((k.lower(), html.unescape(v1 or v2 or "")) for k, v1, v2 in re.findall(r"""([\w:.-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')""", im.group(1)))
        if a.get("name") and not (a.get("type", "text").lower() in ("checkbox", "radio") and not re.search(r"\bchecked\b", im.group(1))):
            fields[a["name"]] = a.get("value", "")
    cnt = text_by_id(page, "win0divHRS_AGNT_RSLT_Irowcnt$0")
    total = None
    if cnt:
        norm = re.sub(r"(\d)[\s .,](?=\d{3}(?:\D|$))", r"\1", cnt)
        m = re.search(r"of\s+(\d+)", norm, re.I) or None
        nums = re.findall(r"\d+", norm)
        total = int(m.group(1)) if m else (int(nums[-1]) if nums else None)
    rows = []
    for idx in re.findall(r"""\bid=["']?HRS_AGNT_RSLT_I\$0_row_(\d+)""", page):
        jid = text_by_id(page, f"HRS_APP_JBSCH_I_HRS_JOB_OPENING_ID${idx}")
        title = text_by_id(page, f"SCH_JOB_TITLE${idx}")
        if jid and title:
            rows.append({"id": jid, "title": title, "location": text_by_id(page, f"LOCATION${idx}") or "",
                         "department": text_by_id(page, f"HRS_APP_JBSCH_I_HRS_DEPT_DESCR${idx}") or "",
                         "posted": _date(text_by_id(page, f"SCH_OPENED${idx}"))})
    if total is not None and total < len(rows):
        total = None
    return {"valid": True, "rows": rows, "total": total, "action": act.group(1) if act else None, "fields": fields}


class PeopleSoft(Provider):
    name = "peoplesoft"
    wave = "W2"
    kind = "ats"
    tenant = True
    hosts = ()

    def detect(self, careers_url: str):
        c = _cfg(careers_url)
        if not c:
            return None
        return Target(slug=c["site"], careers_url=careers_url, api_url=_search_url(c))

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        c = _cfg(target.api_url) or _cfg(target.careers_url)
        if not c:
            raise ProviderError("peoplesoft needs an https /psc/<site>/EMPLOYEE/HRMS/c/HRS_HRAM_FL.HRS_CG_SEARCH_FL.GBL url")
        headers = dict(BROWSER)
        r = ctx.http.get(_search_url(c), headers=headers)
        pair = (r.headers.get("set-cookie") or "").split(";", 1)[0].strip()
        if "=" in pair:
            headers["Cookie"] = pair
        state = parse_search(r.text)
        if not state["valid"]:
            raise ProviderError("peoplesoft: unrecognized search response (login/challenge page?)")
        rows: dict[str, dict] = {r_["id"]: r_ for r_ in state["rows"]}
        total = state["total"]
        for _ in range(MAX_LOAD_MORE):
            if (total is not None and len(rows) >= total) or len(rows) >= ctx.max_jobs:
                break
            url = urljoin(c["origin"], state["action"]) if state["action"] else _search_url(c)
            if urlsplit(url).netloc != urlsplit(c["origin"]).netloc:
                break
            body = urlencode({**state["fields"], "ICAction": LOAD_MORE})
            resp = ctx.http.post(url, data=body, headers={**headers, "Content-Type": "application/x-www-form-urlencoded"})
            nxt = parse_search(resp.text)
            if not nxt["valid"]:
                break
            total = nxt["total"] if nxt["total"] is not None else total
            fresh = 0
            for r_ in nxt["rows"]:
                if r_["id"] not in rows:
                    rows[r_["id"]] = r_
                    fresh += 1
            state = nxt
            if not fresh:
                break
        company = target.company or c["site"]
        return [self.job(title=r_["title"], url=_detail_url(c, r_["id"]), company=company, location=r_["location"],
                         department=r_["department"], posted_at=r_["posted"], source_id=r_["id"]).validate()
                for r_ in list(rows.values())[: ctx.max_jobs]]


PROVIDER = PeopleSoft()
