import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

V2 = {"count": 1, "positions": [{"id": 563012, "name": "Software Engineer II", "ats_job_id": "R-77",
      "location": "Redmond, WA", "locations": ["Redmond, WA", "Remote - US"], "t_create": 1762300800,
      "canonicalPositionUrl": "https://acme.eightfold.ai/careers/job/563012"}]}
PCSX = {"data": {"count": 1, "positions": [{"id": 9, "name": "Analyst", "location": "Paris", "postedTs": 1762300800}]}}
URL = "https://acme.eightfold.ai/careers?domain=acme.com"


class TestEightfold(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("eightfold")

    def test_detect(self):
        t = self.p.detect(URL)
        self.assertIn("domain=acme.com", t.api_url)
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch_v2(self):
        jobs = self.p.fetch(Target(company="Acme", careers_url=URL), ctx_with({"/api/apply/v2/jobs": V2}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.source), ("Software Engineer II", "Redmond, WA · Remote - US", "eightfold"))
        self.assertEqual(j.url, "https://acme.eightfold.ai/careers/job/563012")
        self.assertTrue(j.posted_at.startswith("2025-11-05"))

    def test_fetch_pcsx_fallback(self):
        ctx = ctx_with({"/api/apply/v2/jobs": (403, "no"), "/api/pcsx/search": PCSX})
        jobs = self.p.fetch(Target(company="Acme", careers_url=URL), ctx)
        self.assertEqual(jobs[0].title, "Analyst")
        self.assertIn("pid=9", jobs[0].url)


if __name__ == "__main__":
    unittest.main()
