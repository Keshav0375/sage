import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"SearchResult": {"SearchResultCountAll": 1, "SearchResultItems": [{
    "MatchedObjectId": "99001",
    "MatchedObjectDescriptor": {
        "PositionID": "99001", "PositionTitle": "Elektroniker &amp; Techniker (m/w/d)",
        "PositionURI": "https://acme.beesite.de/jobposting/99001",
        "PositionLocation": [{"CityName": "Stuttgart"}, {"CityName": "Ulm"}],
        "PublicationStartDate": "2026-10-09",
    }}]}}


class TestBeeSite(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("beesite")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.beesite.de/").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"acme.beesite.de/search": FIXTURE})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://acme.beesite.de/"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Elektroniker & Techniker (m/w/d)")
        self.assertEqual(j.url, "https://acme.beesite.de/jobposting/99001")
        self.assertEqual(j.location, "Stuttgart / Ulm")
        self.assertTrue(j.posted_at.startswith("2026-10-09"))
        self.assertEqual(j.source, "beesite")


if __name__ == "__main__":
    unittest.main()
