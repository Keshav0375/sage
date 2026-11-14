import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

PAGE = "<script>new Listing({ organizationId : 1, domainId : 2468, getParams : {} })</script>"
API = {"success": True, "data": {"jobCount": 1, "jobs": [{
    "id": 5551, "title": "Maintenance Technician", "jobLocation": "Boise, ID",
    "startDateRef": "2026-10-04 08:00:00", "minSalary": "50000", "maxSalary": "60000", "payTypeFrame": "per year",
}]}}


class TestApplicantPro(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("applicantpro")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.applicantpro.com/jobs/").slug, "acme")
        self.assertEqual(self.p.detect("https://www.applicantpro.com/openings/zed/jobs/1").slug, "zed")
        self.assertIsNone(self.p.detect("https://www.applicantpro.com/"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"/core/jobs/2468": API, "acme.applicantpro.com/jobs/": PAGE})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://acme.applicantpro.com/jobs/"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Maintenance Technician")
        self.assertEqual(j.url, "https://acme.applicantpro.com/jobs/5551")
        self.assertEqual(j.location, "Boise, ID")
        self.assertEqual((j.salary_min, j.salary_max), (50000.0, 60000.0))
        self.assertTrue(j.posted_at.startswith("2026-10-04"))
        self.assertEqual(j.source, "applicantpro")


if __name__ == "__main__":
    unittest.main()
