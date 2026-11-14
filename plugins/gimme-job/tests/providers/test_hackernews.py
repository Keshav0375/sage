import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

SEARCH = {"hits": [
    {"objectID": "111", "title": "Ask HN: Who wants to be hired? (November 2026)"},
    {"objectID": "222", "title": "Ask HN: Who is hiring? (November 2026)"}]}
THREAD = {"id": 222, "children": [
    {"id": 301, "created_at": "2026-11-02T10:00:00.000Z",
     "text": 'Acme | Senior Engineer | Toronto, ON | REMOTE | <a href="https://boards.greenhouse.io/acme/jobs/1">apply</a><p>We build rockets.'},
    {"id": 302, "created_at": "2026-11-02T11:00:00.000Z", "text": "Globex | Remote | Designer<p>Email us at jobs@globex.test"},
    {"id": 303, "deleted": True, "text": "gone"},
]}


class TestHackerNews(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("hackernews")

    def test_detect_none(self):
        self.assertIsNone(self.p.detect("https://news.ycombinator.com/"))

    def test_fetch(self):
        ctx = ctx_with({"search_by_date": SEARCH, "api/v1/items/222": THREAD})
        jobs = self.p.fetch(Target(), ctx)
        self.assertEqual(len(jobs), 2)
        a, b = jobs
        self.assertEqual((a.company, a.location, a.url, a.source), ("Acme", "Toronto, ON", "https://boards.greenhouse.io/acme/jobs/1", "hackernews"))
        self.assertIn("rockets", a.description)
        self.assertEqual((b.company, b.url), ("Globex", "https://news.ycombinator.com/item?id=302"))
        self.assertTrue(a.posted_at.startswith("2026-11-02"))


if __name__ == "__main__":
    unittest.main()

