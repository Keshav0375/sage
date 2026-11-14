import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {
    "locale": "de-DE", "total": 1, "hasNextPage": False,
    "results": [{
        "title": "Verkäufer (m/w/d)", "slugTitle": "verkaeufer-m-w-d", "postingId": 987654,
        "onlineFrom": "2026-10-20T00:00:00Z",
        "locations": [{"city": "Kamen", "country": "Germany"}, {"city": "Bergkamen", "country": "Germany"}],
    }],
}


class TestAldiNord(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("aldi-nord")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://www.aldi-nord.de/karriere.html"))
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"aldi-nord.de/api/job/hr/query": FIXTURE})
        jobs = self.p.fetch(Target(company="ALDI Nord", careers_url="https://www.aldi-nord.de/karriere.html"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://www.aldi-nord.de/karriere/detail/verkaeufer-m-w-d-987654.html")
        self.assertEqual(j.location, "Kamen / Bergkamen, Germany")
        self.assertEqual(j.source, "aldi-nord")
        self.assertTrue(j.posted_at.startswith("2026-10-20"))


if __name__ == "__main__":
    unittest.main()
