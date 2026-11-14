import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

URL = "https://myjobs.adp.com/acmecareers/cx/job-listing"
SITE = {"orgoid": "G3ABCDEF123456", "name": "Acme"}
LIST = {"count": 1, "jobRequisitions": [{"reqId": "5001234", "jobTitle": "Payroll Specialist", "clientRequisitionID": "R-77",
        "requisitionLocations": [{"address": {"cityName": "Roseland", "countrySubdivisionLevel1": {"codeValue": "NJ"}, "country": {"codeValue": "US"}}}]}]}


class TestAdpMyJobs(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("adp-myjobs")

    def test_detect(self):
        self.assertEqual(self.p.detect(URL).slug, "acmecareers")
        self.assertIsNone(self.p.detect("https://myjobs.adp.com/public/x"))
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"/career-site/acmecareers": SITE, "/job-requisitions": LIST})
        jobs = self.p.fetch(Target(company="Acme", careers_url=URL), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.source), ("Payroll Specialist", "Roseland, NJ, US", "adp-myjobs"))
        self.assertEqual(j.url, "https://myjobs.adp.com/acmecareers/cx/job-details?rb=CareerSite&reqId=5001234")


if __name__ == "__main__":
    unittest.main()
