import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

API = "https://www.comeet.co/careers-api/2.0/company/A1.234/positions?token=SECRET&details=false"
RESP = [{"uid": "B7.9C1", "name": "QA Engineer", "department": "R&D", "time_updated": "2026-11-06T08:00:00Z",
         "location": {"name": "Tel Aviv, Israel", "is_remote": False}, "url_active_page": "https://www.comeet.com/jobs/acme/A1.234/qa-engineer/B7.9C1"}]


class TestComeet(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("comeet")

    def test_detect(self):
        self.assertEqual(self.p.detect(API).slug, "A1.234")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(company="Acme", api_url=API), ctx_with({"careers-api/2.0/company/A1.234/positions": RESP}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.department, j.source), ("QA Engineer", "Tel Aviv, Israel", "R&D", "comeet"))
        self.assertTrue(j.url.startswith("https://www.comeet.com/jobs/"))


if __name__ == "__main__":
    unittest.main()
