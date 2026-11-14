import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"data": [{
    "title": "Agentic AI Engineer", "companyName": "Acme AI", "slug": "agentic-ai-engineer-acme",
    "location": "Remote (EU)", "countries": ["DE"], "description": "<p>Build <b>agents</b>.</p>",
    "postedAt": "2026-11-01T10:00:00Z", "salaryMin": 100000, "salaryMax": 150000, "salaryCurrency": "eur",
}], "meta": {"total": 1, "page": 1, "per_page": 50}}


class TestAgenticJobs(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("agentic-jobs")
        jobs = p.fetch(Target(), ctx_with({"agentic-engineering-jobs.com/api/v1/jobs": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Agentic AI Engineer")
        self.assertEqual(j.url, "https://agentic-engineering-jobs.com/jobs/agentic-ai-engineer-acme")
        self.assertEqual((j.company, j.location, j.currency, j.salary_min), ("Acme AI", "Remote (EU)", "EUR", 100000.0))
        self.assertIn("agents", j.description)
        self.assertEqual(j.source, "agentic-jobs")
        self.assertIsNone(p.detect("https://example.com"))


if __name__ == "__main__":
    unittest.main()
