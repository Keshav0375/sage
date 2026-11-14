import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"totalHits": 1, "jobs": [{"data": {
    "id": "55555", "title": "Entwicklungsingenieur U-Boot (m/w/d)", "postingDate_timestamp": 1760000000,
    "locations": [{"cityState": "Kiel, Schleswig-Holstein"}, {"city": "Hamburg"}]}}]}


class TestTkms(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("tkms")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://jobs.tkmsgroup.com/en"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"jobs.tkmsgroup.com/api/filter/query": FIXTURE})
        jobs = self.p.fetch(Target(company="TKMS"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://jobs.tkmsgroup.com/en/job/Entwicklungsingenieur-U-Boot-m-w-d/55555")
        self.assertEqual(j.location, "Kiel, Schleswig-Holstein / Hamburg")
        self.assertTrue(j.posted_at.startswith("2025-"))
        self.assertEqual(j.source, "tkms")


if __name__ == "__main__":
    unittest.main()
