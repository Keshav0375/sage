import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = [{
    "id": "abc-1", "text": "Senior Backend Engineer", "hostedUrl": "https://jobs.lever.co/acme/abc-1",
    "createdAt": 1762000000000, "country": "CA", "workplaceType": "remote",
    "categories": {"location": "Toronto", "allLocations": ["Toronto", "Vancouver"], "team": "Eng", "commitment": "Full-time"},
    "descriptionPlain": "Build things.", "lists": [{"text": "Requirements", "content": "<li>Python</li>"}],
    "additionalPlain": "Equal opportunity.",
    "salaryRange": {"min": 100000, "max": 150000, "currency": "cad", "interval": "per-year-salary"},
}]


class TestLever(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("lever")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://jobs.lever.co/acme").api_url, "https://api.lever.co/v0/postings/acme")
        self.assertIn("api.eu.lever.co", self.p.detect("https://jobs.eu.lever.co/acme").api_url)
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"api.lever.co/v0/postings/acme": FIXTURE})
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.source, j.workplace), ("Senior Backend Engineer", "Acme", "lever", "remote"))
        self.assertEqual(j.locations, ["Toronto", "Vancouver"])
        self.assertEqual((j.salary_min, j.salary_max, j.currency, j.salary_period), (100000, 150000, "CAD", "year"))
        self.assertIn("Python", j.description)
        self.assertTrue(j.posted_at.startswith("2025-"))


if __name__ == "__main__":
    unittest.main()

