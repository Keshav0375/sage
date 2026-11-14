import tempfile
import unittest
from datetime import date

from scripts.extract import extract_all, rules_confidence, archive, closing, fingerprint, reposts
from scripts.extract.fetch_jd import fetch
from scripts.providers._http import FakeTransport, Http
from . import fixtures as F


class ExtractAllTests(unittest.TestCase):
    def test_tr(self):
        r = extract_all(F.TR, {"title": "Senior AI Engineer"})
        self.assertEqual(r["level"], "senior")
        self.assertEqual(r["salary_max"], 145000)
        self.assertEqual(r["workplace"], "hybrid")
        self.assertEqual(r["years_min"], 2)
        self.assertGreaterEqual(rules_confidence(r), 0.8)

    def test_all_fixtures_no_crash(self):
        for t in (F.CGI, F.ERICSSON, F.FIRSTNATIONAL, F.WSP):
            self.assertIsInstance(extract_all(t), dict)

    def test_low_confidence(self):
        self.assertEqual(extract_all(""), {})
        self.assertEqual(rules_confidence({}), 0.0)
        self.assertLess(rules_confidence(extract_all("Join our team! We love people.")), 0.3)


class FingerprintTests(unittest.TestCase):
    def test_stable(self):
        a = {"title": "Senior AI Engineer (m/f/d)", "company": "Acme Inc.", "location": "Toronto, ON"}
        b = {"title": "senior ai engineer - Remote", "company": "ACME", "city": "toronto"}
        self.assertEqual(fingerprint.fingerprint(a), fingerprint.fingerprint(b))
        self.assertNotEqual(fingerprint.fingerprint(a), fingerprint.fingerprint({**a, "company": "Other"}))
        self.assertEqual(fingerprint.text_hash("Hello  World\n"), fingerprint.text_hash("hello world"))


class RepostTests(unittest.TestCase):
    def test_flags(self):
        today = date(2026, 11, 14)
        hist = [{"id": "old", "title": "AI Engineer", "company": "Acme", "location": "Toronto", "posted_at": "2026-10-01"},
                {"id": "ancient", "title": "ML Engineer", "company": "Acme", "location": "Toronto", "posted_at": "2025-01-01"}]
        jobs = [{"id": "new", "title": "AI Engineer", "company": "Acme", "location": "Toronto, ON", "posted_at": "2026-11-10"},
                {"id": "old", "title": "AI Engineer", "company": "Acme", "location": "Toronto"},
                {"id": "ml", "title": "ML Engineer", "company": "Acme", "location": "Toronto", "posted_at": "2026-11-10"}]
        self.assertEqual(reposts.detect_reposts(jobs, hist, days=90, today=today), ["new"])


class ClosingTests(unittest.TestCase):
    def test_soon(self):
        jobs = [{"id": "a", "closes_at": "2026-11-20"}, {"id": "b", "closes_at": "2026-12-20"},
                {"id": "c", "closes_at": "2026-11-01"}, {"id": "d"}]
        self.assertEqual(closing.closing_soon(jobs, 7, date(2026, 11, 14)), ["a"])


class ArchiveTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            h = archive.save("some JD text", d)
            self.assertEqual(archive.save("some JD text", d), h)
            self.assertEqual(archive.load(h, d), "some JD text")
            self.assertIsNone(archive.load("0" * 40, d))


class FetchTests(unittest.TestCase):
    def test_jsonld_first(self):
        import json
        desc = "<p>" + "Build agentic systems. " * 20 + "</p><ul><li>Python</li></ul>"
        html = ('<html><body><nav>menu</nav><script type="application/ld+json">%s</script></body></html>'
                % json.dumps({"@type": "JobPosting", "title": "AI Engineer", "description": desc}))
        http = Http(FakeTransport({"/job/1": html}))
        r = fetch("https://x.example/job/1", http)
        self.assertEqual((r["status"], r["source"], r["title"]), (200, "jsonld", "AI Engineer"))
        self.assertIn("- Python", r["text"])
        self.assertEqual(r["html_len"], len(html))

    def test_html_fallback_and_404(self):
        body = "<html><body><nav>skip me</nav><main>" + "<p>Real job text here.</p>" * 30 + "</main></body></html>"
        http = Http(FakeTransport({"/job/2": body}))
        r = fetch("https://x.example/job/2", http)
        self.assertEqual(r["source"], "html")
        self.assertNotIn("skip me", r["text"])
        r = fetch("https://x.example/missing", http)
        self.assertEqual((r["status"], r["text"]), (404, ""))
