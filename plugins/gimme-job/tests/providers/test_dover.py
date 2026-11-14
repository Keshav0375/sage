import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

BOARD = "11111111-2222-3333-4444-555555555555"
URL = f"https://app.dover.com/Acme/careers/{BOARD}"
RESP = {"results": [
    {"id": "aaaa-1", "title": "Founding Engineer", "is_published": True, "workplace_type": "HYBRID",
     "locations": [{"name": "SF", "is_primary": True, "location_type": "HYBRID", "location_option": {"display_name": "San Francisco, CA"}}]},
    {"id": "aaaa-2", "title": "Sample", "is_sample": True}], "next": None}


class TestDover(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("dover")

    def test_detect(self):
        self.assertEqual(self.p.detect(URL).slug, BOARD)
        self.assertIsNone(self.p.detect("https://app.dover.com/Acme/careers/notauuid"))
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(company="Acme", careers_url=URL), ctx_with({"careers-page/": RESP}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.source), ("Founding Engineer", "San Francisco, CA (Hybrid)", "dover"))
        self.assertEqual(j.url, "https://app.dover.com/apply/Acme/aaaa-1")


if __name__ == "__main__":
    unittest.main()
