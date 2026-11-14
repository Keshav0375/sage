"""Explicit recruiter / hiring-manager contacts (public emails only, never guessed)."""
from __future__ import annotations

import re

_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}")
_SKIP_LOCAL = re.compile(r"^(?:no-?reply|do-?not-?reply|donotreply|privacy|unsubscribe|abuse|legal|dpo|accessibility|accommodations?)", re.I)
_NAME = r"[A-Z][a-zA-Z'’\-]+(?:\s+[A-Z][a-zA-Z'’\-]+){1,2}"
_TITLE = r"[A-Za-z&/ ]{0,40}?(?:Recruiter|Recruitment|Talent Acquisition|Hiring Manager|Manager|Lead|Director|Partner|Specialist|Sourcer|Coordinator)"
_NAME_TITLE = re.compile(r"(" + _NAME + r")\s*(?:,|-|–|\()\s*(" + _TITLE + r")\)?")
_TITLE_NAME = re.compile(r"(" + _TITLE + r")\s*[:\-–]\s*(" + _NAME + r")")
_CONTACT_NAME = re.compile(r"(?:contact|reach out to|email|send (?:your )?(?:resume|cv) to|recruiter|hiring manager)\s*[:\-]?\s*(" + _NAME + r")")


def extract(text: str, job: dict | None = None) -> dict:
    text = text or ""
    seen: set[str] = set()
    contacts = []
    for m in _EMAIL.finditer(text):
        email = m.group(0).rstrip(".").lower()
        if email in seen or _SKIP_LOCAL.match(email.split("@")[0]):
            continue
        seen.add(email)
        ctx = text[max(0, m.start() - 140): m.end() + 60]
        line = text[text.rfind("\n", 0, m.start()) + 1: (text.find("\n", m.end()) if "\n" in text[m.end():] else len(text))]
        c: dict = {"email": email}
        for scope in (line, ctx):
            nt = _NAME_TITLE.search(scope)
            if nt:
                c["name"], c["title"] = nt.group(1).strip(), nt.group(2).strip()
                break
            tn = _TITLE_NAME.search(scope)
            if tn:
                c["title"], c["name"] = tn.group(1).strip(), tn.group(2).strip()
                break
            cn = _CONTACT_NAME.search(scope)
            if cn:
                c["name"] = cn.group(1).strip()
                break
        contacts.append({"name": c.get("name", ""), "title": c.get("title", ""), "email": email})
    return {"contacts": contacts} if contacts else {}
