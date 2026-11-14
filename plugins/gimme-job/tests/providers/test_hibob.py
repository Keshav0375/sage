import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {
    "filterGroups": [],
    "jobAdDetails": [
        {
            "id": "7c2e-uuid-1", "title": "Account Executive", "site": "Berlin", "country": "Germany",
            "workspaceTypeId": "remote", "publishedAt": "2026-10-01T09:00:00Z", "language": "en",
            "description": "<p>Sell things</p>", "requirements": "<p>Experience</p>",
            "payTransparencyMinSalary": 48000, "payTransparencyMaxSalary": 55000,
            "payTransparencySalaryCurrency": "eur", "payTransparencySalaryPayPeriod": "Annual",
        }
    ],
    "jobOpeningMetadata": {},
}


class TestHibob(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("hibob")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.careers.hibob.com/jobs").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"acme.careers.hibob.com/api/job-ad": FIXTURE})
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Account Executive")
        self.assertEqual(j.url, "https://acme.careers.hibob.com/jobs/7c2e-uuid-1")
        self.assertEqual(j.source, "hibob")
        self.assertEqual(j.location, "Berlin, Germany, Remote")
        self.assertEqual(j.salary_min, 48000)
        self.assertEqual(j.currency, "EUR")
        self.assertIn("Sell things", j.description)


if __name__ == "__main__":
    unittest.main()
