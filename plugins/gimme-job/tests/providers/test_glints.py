import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.glints import PROVIDER

FIXTURE = {"data": {"searchJobsV3": {"hasMore": False, "jobsInPage": [{
    "id": "abc-123", "title": "Data Engineer", "company": {"name": "Acme Indonesia", "brandName": "Acme"},
    "city": {"name": "Jakarta Selatan"}, "country": {"code": "ID", "name": "Indonesia"},
    "salaries": [{"salaryType": "MONTHLY", "salaryMode": "BASIC", "minAmount": 8000000, "maxAmount": 12000000, "CurrencyCode": "IDR"}],
    "createdAt": "2026-10-20T03:00:00.000Z"}]}}}


class TestGlints(unittest.TestCase):
    def test_fetch(self):
        jobs = PROVIDER.fetch(Target(query="data"), ctx_with({"glints.com/api/v2-alc/graphql": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.country), ("Data Engineer", "Acme Indonesia", "Jakarta Selatan", "ID"))
        self.assertEqual(j.url, "https://glints.com/id/opportunities/jobs/abc-123")
        self.assertEqual((j.salary_min, j.salary_max, j.currency, j.salary_period), (8000000, 12000000, "IDR", "month"))


if __name__ == "__main__":
    unittest.main()
