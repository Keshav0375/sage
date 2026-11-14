import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import ProviderError, Target

FIXTURE = {"results": [{
    "title": "Data Engineer",
    "metadata": {"jobPostId": "MCF-2026-0001", "newPostingDate": "2026-11-10",
                 "jobDetailsUrl": "https://www.mycareersfuture.gov.sg/job/information-technology/data-engineer-abc123"},
    "postedCompany": {"name": "Acme Pte Ltd"},
    "address": {"districts": [{"location": "Central"}, {"location": "Jurong"}]},
    "salary": {"minimum": 6000, "maximum": 9000},
}, {"title": "Bad", "metadata": {"jobPostId": "x", "jobDetailsUrl": "https://evil.example/x"}}]}


class TestMyCareersFuture(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("mycareersfuture")

    def test_fetch(self):
        jobs = self.p.fetch(Target(query="data"), ctx_with({"api.mycareersfuture.gov.sg/v2/search": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Data Engineer", "Acme Pte Ltd", "Central, Jurong"))
        self.assertEqual(j.source, "mycareersfuture")
        self.assertEqual(j.salary_max, 9000)

    def test_needs_query(self):
        with self.assertRaises(ProviderError):
            self.p.fetch(Target(), ctx_with({}))


if __name__ == "__main__":
    unittest.main()
