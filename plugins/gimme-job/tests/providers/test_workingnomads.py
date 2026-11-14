import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = [{"title": "Senior Django Dev", "url": "https://www.workingnomads.com/jobs/senior-django-dev-acme",
            "company_name": "Acme", "location": "Anywhere", "pub_date": "2026-10-29T09:50:51-04:00",
            "category_name": "Development", "description": "<p>Python &amp; Django</p>"},
           {"title": "", "url": "https://x.example/1"}]


class TestWorkingNomads(unittest.TestCase):
    def test_fetch(self):
        jobs = _registry.get("workingnomads").fetch(Target(), ctx_with({"workingnomads.com/api/exposed_jobs": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.department), ("Senior Django Dev", "Acme", "Anywhere", "Development"))
        self.assertIn("Python & Django", j.description)
        self.assertTrue(j.posted_at.startswith("2026-10-29"))


if __name__ == "__main__":
    unittest.main()
