import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"apiVersion": "1", "jobs": [{
    "id": "uuid-1", "title": "Product Designer", "jobUrl": "https://jobs.ashbyhq.com/acme/uuid-1",
    "location": "Remote - Canada", "secondaryLocations": [{"location": "Toronto"}],
    "department": "Design", "employmentType": "FullTime", "workplaceType": "Remote", "isRemote": True,
    "publishedAt": "2026-10-20T12:00:00.000+00:00", "descriptionPlain": "Design.",
    "compensation": {"compensationTiers": [{"components": [
        {"compensationType": "Salary", "interval": "1 YEAR", "currencyCode": "USD", "minValue": 120000, "maxValue": 160000}]}]},
}]}


class TestAshby(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("ashby")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://jobs.ashbyhq.com/acme").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"api.ashbyhq.com/posting-api/job-board/acme": FIXTURE})
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.source, j.workplace, j.employment), ("Product Designer", "ashby", "remote", "fulltime"))
        self.assertEqual(j.locations, ["Remote - Canada", "Toronto"])
        self.assertEqual((j.salary_min, j.salary_max, j.currency), (120000, 160000, "USD"))
        self.assertTrue(j.posted_at.startswith("2026-10-20"))


if __name__ == "__main__":
    unittest.main()

