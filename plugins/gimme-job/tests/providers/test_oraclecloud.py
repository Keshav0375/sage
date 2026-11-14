import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

URL = "https://eacme.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs"
RESP = {"items": [{"TotalJobsCount": 1, "requisitionList": [
    {"Id": "55012", "Title": "Treasury Analyst", "PostedDate": "2026-11-05", "PrimaryLocation": "Austin, TX, United States",
     "WorkplaceTypeCode": "ORA_HYBRID", "ShortDescriptionStr": "Manage &amp; forecast cash."}]}]}


class TestOracleCloud(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("oraclecloud")

    def test_detect(self):
        t = self.p.detect(URL)
        self.assertEqual(t.slug, "CX_1001")
        self.assertIn("siteNumber=CX_1001", t.api_url)
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"recruitingCEJobRequisitions": RESP})
        jobs = self.p.fetch(Target(company="Acme", careers_url=URL), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.workplace, j.source), ("Treasury Analyst", "Austin, TX, United States", "hybrid", "oraclecloud"))
        self.assertEqual(j.url, "https://eacme.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/55012")
        self.assertEqual(j.description, "Manage & forecast cash.")


if __name__ == "__main__":
    unittest.main()
