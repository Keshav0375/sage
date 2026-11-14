import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

RESP = {"items": [{"id": 4521, "title": "Growth  Marketer", "job_post_url": "https://jobs.polymer.co/acme/4521",
                   "display_location": "", "city": "Lisbon", "country": "Portugal", "remoteness_pretty": "Remote",
                   "published_at": "2026-11-02T09:00:00Z"}], "meta": {"is_last": True, "count": 1}}


class TestPolymer(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("polymer")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://jobs.polymer.co/acme").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx_with({"organizations/acme/jobs?page=1": RESP}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.url, j.source), ("Growth Marketer", "Remote (Lisbon, Portugal)", "https://jobs.polymer.co/acme/4521", "polymer"))


if __name__ == "__main__":
    unittest.main()
