import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

URL = "https://recruiting2.ultipro.com/ACM1000ACME/JobBoard/0a1b2c3d-0000-4000-8000-123456789abc/?q=&o=postedDateDesc"
RESP = {"totalCount": 1, "opportunities": [{"Id": "5f1e-77", "Title": "Warehouse Associate", "PostedDate": "2026-11-05T14:30:00Z",
        "BriefDescription": "<p>Pick &amp; pack.</p>",
        "Locations": [{"Address": {"City": "Reno", "State": {"Code": "NV"}}, "LocalizedName": "Reno DC"}]}]}


class TestUltiPro(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("ultipro")

    def test_detect(self):
        self.assertEqual(self.p.detect(URL).slug, "ACM1000ACME")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(company="Acme", careers_url=URL), ctx_with({"LoadSearchResults": RESP}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.source, j.description), ("Warehouse Associate", "Reno, NV", "ultipro", "Pick & pack."))
        self.assertTrue(j.url.endswith("OpportunityDetail?opportunityId=5f1e-77"))


if __name__ == "__main__":
    unittest.main()
