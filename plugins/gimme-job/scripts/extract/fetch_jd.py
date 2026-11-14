"""Fetch a job page and return the JD text (JSON-LD description first, then main HTML text)."""
from __future__ import annotations

import re

from ..providers._parse import html_to_text, json_ld_jobs


def _main_html(html: str) -> str:
    for tag in ("main", "article"):
        m = re.search(r"<%s\b[^>]*>(.*?)</%s>" % (tag, tag), html, re.S | re.I)
        if m and len(m.group(1)) > 400:
            return m.group(1)
    html = re.sub(r"<(nav|header|footer|aside|form)\b.*?</\1>", " ", html, flags=re.S | re.I)
    m = re.search(r"<body\b[^>]*>(.*)</body>", html, re.S | re.I)
    return m.group(1) if m else html


def fetch(url: str, http) -> dict:
    r = http.get(url, ok=tuple(range(200, 600)))
    html = r.text
    out = {"url": url, "text": "", "html_len": len(html), "status": r.status}
    if r.status >= 400:
        return out
    for jp in json_ld_jobs(html):
        desc = html_to_text(str(jp.get("description") or ""))
        if len(desc) >= 200:
            out["text"] = desc
            out["source"] = "jsonld"
            if jp.get("title"):
                out["title"] = str(jp["title"])
            return out
    out["text"] = html_to_text(_main_html(html))
    out["source"] = "html"
    return out
