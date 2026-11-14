import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.kalibrr import PROVIDER

FIXTURE = {"count": 1, "jobs": [{
    "id": 998877, "name": "Backend Engineer", "slug": "backend-engineer", "company": {"code": "Acme", "name": "Acme PH"},
    "google_location": {"address_components": {"city": "Makati", "region": "Metro Manila", "country": "Philippines"}},
    "is_work_from_home": False, "description": "<p>Build things</p>", "qualifications": "<ul><li>Python</li></ul>",
    "activation_date": "2026-10-19T00:00:00Z"}]}


class TestKalibrr(unittest.TestCase):
    def test_fetch(self):
        jobs = PROVIDER.fetch(Target(query="backend"), ctx_with({"kalibrr.com/kjs/job_board/search": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Backend Engineer", "Acme PH", "Makati, Metro Manila, Philippines"))
        self.assertEqual(j.url, "https://www.kalibrr.com/c/Acme/jobs/998877/backend-engineer")
        self.assertIn("Python", j.description)


if __name__ == "__main__":
    unittest.main()
