import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"payload": {"hasMore": False, "jobs": [
    {"id": 101, "name": "Frontend Engineer", "path": "/companies/acme/jobs/101",
     "company": {"brand": "Acme"}, "location": "台北市"},
    {"id": 102, "name": "Backend Engineer", "thirdPartyUrl": "https://acme.example/jobs/2?utm_source=y&ref=1&utm_medium=x",
     "company": {"brand": "Beta"}, "location": "新竹市"},
]}}


class TestYourator(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("yourator")
        jobs = p.fetch(Target(), ctx_with({"yourator.co/api/v4/jobs": FIXTURE}))
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0].url, "https://www.yourator.co/companies/acme/jobs/101")
        self.assertEqual((jobs[0].company, jobs[0].location), ("Acme", "台北市"))
        self.assertEqual(jobs[1].url, "https://acme.example/jobs/2?ref=1")


if __name__ == "__main__":
    unittest.main()
