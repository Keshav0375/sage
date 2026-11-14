"""Notion-hosted careers pages (*.notion.site) — public v3 API (no auth).

POST {origin}/api/v3/loadPageChunk -> recordMap.block ; a plain page lists child pages, a database page
is followed by POST {origin}/api/v3/queryCollection (view filter applied) -> blockIds.
Tenant = careers_url like https://acme.notion.site/Careers-<32hex>[?v=<view>].
Mechanism from career-ops providers/notion.mjs (MIT); code is our own.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlsplit

from ._base import Context, Job, Provider, ProviderError, Target

HOST_RE = re.compile(r"^[a-z0-9-]+\.notion\.site$")
UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")
PAGE_ID_RE = re.compile(r"[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}", re.I)
COLLECTION_TYPES = {"collection_view_page", "collection_view"}
ROW_LIMIT = 200
MAX_DEPTH = 3


def _uuid(raw: str):
    h = raw.replace("-", "").lower()
    if not re.fullmatch(r"[0-9a-f]{32}", h):
        return None
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:]}"


def resolve_page(careers_url: str):
    p = urlsplit(careers_url or "")
    if p.scheme != "https" or not HOST_RE.match((p.hostname or "").lower()):
        return None
    ids = PAGE_ID_RE.findall(p.path)
    page_id = _uuid(ids[-1]) if ids else None
    if not page_id:
        return None
    v = (parse_qs(p.query).get("v") or [""])[0]
    return {"origin": f"https://{p.hostname.lower()}", "page_id": page_id, "view_id": _uuid(v) if v else None}


def _rec(r):
    v = r.get("value") if isinstance(r, dict) else None
    if isinstance(v, dict) and isinstance(v.get("value"), dict) and "role" in v:
        return v["value"]
    return v if isinstance(v, dict) else None


def _rich(prop) -> str:
    if not isinstance(prop, list):
        return ""
    return "".join(s[0] for s in prop if isinstance(s, list) and s and isinstance(s[0], str)).strip()


def _mentions(prop) -> list[str]:
    out = []
    for seg in prop if isinstance(prop, list) else []:
        for a in (seg[1] if isinstance(seg, list) and len(seg) > 1 and isinstance(seg[1], list) else []):
            if isinstance(a, list) and len(a) > 1 and a[0] == "p" and isinstance(a[1], str):
                out.append(a[1])
    return out


class Notion(Provider):
    name = "notion"
    wave = "W3"
    kind = "ats"
    tenant = True
    hosts = ("notion.site",)

    def detect(self, careers_url: str):
        pg = resolve_page(careers_url)
        return Target(careers_url=careers_url, api_url=f"{pg['origin']}/api/v3/loadPageChunk") if pg else None

    def _job(self, block, origin: str, company: str, location: str = ""):
        if not isinstance(block, dict) or block.get("alive") is False:
            return None
        title = _rich((block.get("properties") or {}).get("title"))
        bid = block.get("id")
        if not title or not isinstance(bid, str) or not UUID_RE.match(bid):
            return None
        ct = block.get("created_time")
        posted = datetime.fromtimestamp(ct / 1000, tz=timezone.utc).isoformat() if isinstance(ct, (int, float)) and ct > 0 else ""
        return self.job(title=title, url=f"{origin}/{bid.replace('-', '')}", company=company,
                        location=location, posted_at=posted, source_id=bid).validate()

    def fetch(self, target: Target, ctx: Context) -> list[Job]:
        pg = resolve_page(target.careers_url)
        if not pg:
            raise ProviderError("notion: cannot derive a page id from careers_url")
        origin, page_id = pg["origin"], pg["page_id"]
        company = target.company or origin.split("//")[1].split(".")[0]

        def post(path, body):
            return ctx.http.post_json(f"{origin}/api/v3/{path}", data=body)

        chunk = post("loadPageChunk", {"pageId": page_id, "limit": 100, "cursor": {"stack": []},
                                       "chunkNumber": 0, "verticalColumns": False})
        rm = chunk.get("recordMap") if isinstance(chunk, dict) else None
        blocks = (rm or {}).get("block")
        if not isinstance(blocks, dict):
            raise ProviderError("notion: expected recordMap.block")
        root = _rec(blocks.get(page_id))
        if not root:
            raise ProviderError(f"notion: page {page_id} not in response (not public?)")
        content = root.get("content") if isinstance(root.get("content"), list) else []
        db = root if root.get("type") in COLLECTION_TYPES else next(
            (b for b in (_rec(blocks.get(i)) for i in content) if b and b.get("type") in COLLECTION_TYPES), None)

        if db:
            cid = db.get("collection_id") or (db.get("format") or {}).get("collection_pointer", {}).get("id")
            view_ids = db.get("view_ids") if isinstance(db.get("view_ids"), list) else []
            view_id = pg["view_id"] if pg["view_id"] in view_ids else (view_ids[0] if view_ids else None)
            space = db.get("space_id") or (blocks.get(page_id) or {}).get("spaceId")
            if not (isinstance(cid, str) and isinstance(view_id, str) and isinstance(space, str)):
                raise ProviderError("notion: database block missing collection_id/view_ids/space_id")
            view = _rec((rm.get("collection_view") or {}).get(view_id))
            if not view:
                raise ProviderError("notion: view not in response")
            q2 = view.get("query2") or {}
            loader = {"type": "reducer", "reducers": {"collection_group_results": {"type": "results", "limit": ROW_LIMIT}},
                      "sort": q2.get("sort") if isinstance(q2.get("sort"), list) else [],
                      "searchQuery": "", "userTimeZone": "UTC"}
            if isinstance(q2.get("filter"), dict):
                loader["filter"] = q2["filter"]
            res = post("queryCollection?src=initial_load", {
                "source": {"type": "collection", "id": cid, "spaceId": space},
                "collectionView": {"id": view_id, "spaceId": space}, "loader": loader})
            ids = (((res.get("result") or {}).get("reducerResults") or {}).get("collection_group_results") or {}).get("blockIds") \
                if isinstance(res, dict) else None
            if not isinstance(ids, list):
                raise ProviderError("notion: expected collection_group_results.blockIds[]")
            rblocks = (res.get("recordMap") or {}).get("block") or {}
            schema = (_rec(((res.get("recordMap") or {}).get("collection") or {}).get(cid)) or {}).get("schema") or {}
            lkey = next((k for k, v in schema.items() if re.fullmatch(r"locations?", str((v or {}).get("name", "")).strip(), re.I)), None)
            multi = bool(lkey) and (schema[lkey] or {}).get("type") == "multi_select"
            jobs = []
            for i in ids:
                b = _rec(rblocks.get(i))
                raw = _rich(((b or {}).get("properties") or {}).get(lkey)) if lkey else ""
                loc = " · ".join(s.strip() for s in raw.split(",") if s.strip()) if multi else raw
                j = self._job(b, origin, company, loc)
                if j:
                    jobs.append(j)
                if len(jobs) >= ctx.max_jobs:
                    break
            return jobs

        if root.get("type") != "page":
            raise ProviderError(f"notion: block is a {root.get('type')!r}, not a page or database")
        jobs, seen = [], set()

        def add(block):
            if not isinstance(block, dict) or block.get("type") != "page" or block.get("id") in seen:
                return
            seen.add(block.get("id"))
            j = self._job(block, origin, company)
            if j:
                jobs.append(j)

        def walk(ids, depth):
            for i in ids:
                b = _rec(blocks.get(i)) if blocks.get(i) else None
                if not b or b.get("alive") is False:
                    continue
                if b.get("type") == "page":
                    add(b)
                    continue
                if b.get("type") == "alias":
                    add(_rec(blocks.get(((b.get("format") or {}).get("alias_pointer") or {}).get("id"))))
                    continue
                for m in _mentions((b.get("properties") or {}).get("title")):
                    add(_rec(blocks.get(m)))
                if depth < MAX_DEPTH and isinstance(b.get("content"), list):
                    walk(b["content"], depth + 1)

        walk(content, 0)
        return jobs[: ctx.max_jobs]


PROVIDER = Notion()
