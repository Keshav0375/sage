import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

GUID = "0a1b2c3d-1111-4222-8333-444455556666"
DATA = {"ModuleTitle": "Acme Co", "Jobs": [
    {"JobId": 123456, "JobTitle": "Bookkeeper", "LocationName": "Tulsa, OK", "ShouldDisplayLocation": True, "IsRemote": True,
     "IndeedRemoteType": 1, "PublishedDate": "2026-11-04T09:00:00"},
    {"JobId": 999, "JobTitle": "Internal Only", "IsInternal": True}]}
PAGE = f"<html><script>window.pageData = {json.dumps(DATA)};</script></html>"
URL = f"https://recruiting.paylocity.com/recruiting/jobs/All/{GUID}/Acme-Co"


class TestPaylocity(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("paylocity")

    def test_detect(self):
        self.assertEqual(self.p.detect(URL).slug, GUID)
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(careers_url=URL), ctx_with({"Recruiting/Jobs/All/": PAGE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.workplace, j.source), ("Bookkeeper", "Acme Co", "Tulsa, OK, Hybrid", "hybrid", "paylocity"))
        self.assertEqual(j.url, "https://recruiting.paylocity.com/Recruiting/Jobs/Details/123456")


if __name__ == "__main__":
    unittest.main()
