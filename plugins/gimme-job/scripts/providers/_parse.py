"""Shared parsing helpers for scanners: HTML → text, RSS/Atom, dates, salary text, workplace, JSON paths."""
from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from typing import Any, Iterable, Optional

# ---------------------------------------------------------------- html → text
_BLOCK = {"p", "div", "br", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "section", "article"}


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1
        elif tag == "li":
            self.out.append("\n- ")
        elif tag in _BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.skip = max(0, self.skip - 1)
        elif tag in _BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def html_to_text(s: str) -> str:
    if not s:
        return ""
    if "<" not in s and "&" in s:
        s = html.unescape(s)
    if "&lt;" in s and "<" not in s:
        s = html.unescape(s)
    p = _TextParser()
    p.feed(s)
    text = "".join(p.out)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# ---------------------------------------------------------------- html scraping helpers
class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._href: Optional[str] = None
        self._buf: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._buf = []

    def handle_data(self, data):
        if self._href is not None:
            self._buf.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join("".join(self._buf).split())))
            self._href = None


def links(html_text: str) -> list[tuple[str, str]]:
    """All <a href> links with their visible text."""
    p = _LinkParser()
    p.feed(html_text or "")
    return p.links


def json_ld_jobs(html_text: str) -> list[dict]:
    """schema.org JobPosting objects embedded as JSON-LD."""
    import json
    out: list[dict] = []
    for m in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html_text or "", re.S | re.I):
        try:
            data = json.loads(m.group(1).strip())
        except Exception:
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            d = stack.pop()
            if isinstance(d, dict):
                if d.get("@type") in ("JobPosting", ["JobPosting"]):
                    out.append(d)
                stack.extend(v for k, v in d.items() if k in ("@graph", "itemListElement", "item"))
            elif isinstance(d, list):
                stack.extend(d)
    return out


def next_data(html_text: str) -> Any:
    """Next.js __NEXT_DATA__ payload, or None."""
    import json
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html_text or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


# ---------------------------------------------------------------- RSS / Atom
def feed_items(xml_text: str) -> list[dict[str, str]]:
    """Parse RSS 2.0 or Atom into dicts: title, link, description, published, id, author, categories."""
    xml_text = (xml_text or "").lstrip("﻿").strip()
    if not xml_text:
        return []
    root = ET.fromstring(xml_text)

    def local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    items: list[dict[str, str]] = []
    for el in root.iter():
        name = local(el.tag)
        if name not in ("item", "entry"):
            continue
        d: dict[str, Any] = {"categories": []}
        for c in el:
            n = local(c.tag)
            txt = (c.text or "").strip()
            if n == "link":
                href = c.attrib.get("href")
                if href and (c.attrib.get("rel", "alternate") == "alternate" or "link" not in d):
                    d["link"] = href
                elif txt:
                    d["link"] = txt
            elif n in ("title",):
                d["title"] = html.unescape(txt)
            elif n in ("description", "summary", "content", "encoded"):
                if txt and len(txt) > len(d.get("description", "")):
                    d["description"] = txt
            elif n in ("pubDate", "published", "updated", "date"):
                d.setdefault("published", txt)
            elif n in ("guid", "id"):
                d["id"] = txt
            elif n in ("author", "creator"):
                name_el = next((x for x in c if local(x.tag) == "name"), None)
                d["author"] = (name_el.text if name_el is not None else txt) or ""
            elif n == "category":
                d["categories"].append(txt or c.attrib.get("term", ""))
            else:
                d.setdefault(n, txt)
        items.append(d)
    return items


# ---------------------------------------------------------------- dates
def to_iso(value: Any) -> str:
    """Best-effort ISO 8601 from epoch (s/ms), RFC 822, or ISO strings. '' when unknown."""
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 1e12:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    s = str(value).strip()
    if s.isdigit():
        return to_iso(int(s))
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).isoformat()
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(s).isoformat()
    except (TypeError, ValueError):
        pass
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y", "%B %d, %Y", "%b %d, %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


# ---------------------------------------------------------------- salary
_NUM = r"(\d{1,3}(?:[,\s]\d{3})+|\d+(?:\.\d+)?)\s*([kK])?"
_CUR = {"$": "", "CA$": "CAD", "C$": "CAD", "US$": "USD", "€": "EUR", "£": "GBP", "₹": "INR"}


def parse_salary(text: str) -> dict[str, Any]:
    """'CAD $100,000 - $145,000 per year' → {min, max, currency, period}. {} when no range found."""
    if not text:
        return {}
    t = text.replace("–", "-").replace("—", "-")
    m = re.search(_NUM + r"\s*(?:-|to|–)\s*\$?\s*" + _NUM, t)
    if not m:
        return {}

    def num(v: str, k: Optional[str]) -> float:
        n = float(re.sub(r"[,\s]", "", v))
        return n * 1000 if k else n

    lo, hi = num(m.group(1), m.group(2)), num(m.group(3), m.group(4))
    if lo > hi:
        lo, hi = hi, lo
    cur = ""
    mc = re.search(r"\b(CAD|USD|EUR|GBP|INR|AUD)\b", t, re.I)
    if mc:
        cur = mc.group(1).upper()
    else:
        for sym, code in _CUR.items():
            if sym in t and code:
                cur = code
                break
    period = ""
    tl = t.lower()
    if re.search(r"per hour|/hr|/hour|hourly|an hour", tl):
        period = "hour"
    elif re.search(r"per month|/month|monthly", tl):
        period = "month"
    elif re.search(r"per year|/year|/yr|annual|yearly|a year", tl) or hi >= 20000:
        period = "year"
    return {"salary_min": lo, "salary_max": hi, "currency": cur, "salary_period": period}


# ---------------------------------------------------------------- workplace / employment
def workplace_from(value: Any) -> str:
    """Map a source's dedicated workplace field to remote|hybrid|onsite. Never guess from free text."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "remote" if value else ""
    v = str(value).strip().lower().replace("_", "-").replace(" ", "-")
    if v in ("remote", "fully-remote", "remote-only", "remote-solely", "telecommute", "wfh"):
        return "remote"
    if v in ("hybrid", "flexible", "remote-ok"):
        return "hybrid"
    if v in ("onsite", "on-site", "in-office", "office", "in-person"):
        return "onsite"
    return ""


def employment_from(value: Any) -> str:
    if not value:
        return ""
    v = str(value).strip().lower().replace("_", "").replace("-", "").replace(" ", "")
    if v in ("fulltime", "permanent", "regular", "fte"):
        return "fulltime"
    if v in ("contract", "contractor", "freelance", "temporarycontract", "fixedterm"):
        return "contract"
    if v in ("parttime",):
        return "parttime"
    if v in ("intern", "internship", "coop", "student"):
        return "intern"
    if v in ("temporary", "temp", "seasonal"):
        return "temporary"
    return ""


# ---------------------------------------------------------------- misc
def dig(obj: Any, path: str, default: Any = None) -> Any:
    """dig(d, 'a.b.0.c') safe nested access."""
    cur = obj
    for part in path.split("."):
        if cur is None:
            return default
        if isinstance(cur, list):
            try:
                cur = cur[int(part)]
            except (ValueError, IndexError):
                return default
        elif isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return default
    return default if cur is None else cur


def first(*values: Any) -> Any:
    for v in values:
        if v not in (None, "", [], {}):
            return v
    return ""


def absolute(base: str, href: str) -> str:
    from urllib.parse import urljoin
    return urljoin(base, href or "")


def slug_from_url(url: str, host_suffixes: Iterable[str], position: int = 0) -> str:
    """Return a path segment (or subdomain when position == -1) for URLs on given hosts."""
    from urllib.parse import urlsplit
    p = urlsplit(url or "")
    host = p.netloc.lower()
    if not any(host == h or host.endswith("." + h) for h in host_suffixes):
        return ""
    if position == -1:
        return host.split(".")[0]
    parts = [x for x in p.path.split("/") if x]
    return parts[position] if len(parts) > position else ""
