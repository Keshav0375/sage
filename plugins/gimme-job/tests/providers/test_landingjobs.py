import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.landingjobs import PROVIDER

FIXTURE = [{"id": 5, "title": "Full Stack Engineer", "url": "https://landing.jobs/at/acme-labs/full-stack-engineer",
            "remote": True, "locations": [{"city": "Lisbon", "country_code": "PT"}], "published_at": "2026-10-18T10:00:00Z"}]


class TestLandingJobs(unittest.TestCase):
    def test_fetch(self):
        jobs = PROVIDER.fetch(Target(), ctx_with({"landing.jobs/api/v1/jobs": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.workplace), ("Full Stack Engineer", "Acme Labs", "Lisbon, PT, Remote", "remote"))
        self.assertEqual(j.url, "https://landing.jobs/at/acme-labs/full-stack-engineer")


if __name__ == "__main__":
    unittest.main()
