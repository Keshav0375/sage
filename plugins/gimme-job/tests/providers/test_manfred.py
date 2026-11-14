import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.manfred import PROVIDER

FIXTURE = [
    {"id": 321, "status": "ACTIVE", "position": "Backend Engineer", "slug": "backend-engineer-acme", "company": {"name": "Acme"},
     "locations": ["Madrid"], "remotePercentage": 50, "salaryFrom": 40000, "salaryTo": 55000, "currency": "€"},
    {"id": 322, "status": "CLOSED", "position": "Old", "slug": "old", "company": {"name": "X"}},
]


class TestManfred(unittest.TestCase):
    def test_fetch(self):
        jobs = PROVIDER.fetch(Target(), ctx_with({"getmanfred.com/api/v2/public/offers": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.workplace), ("Backend Engineer", "Acme", "Madrid", "hybrid"))
        self.assertEqual(j.url, "https://www.getmanfred.com/ofertas-empleo/321/backend-engineer-acme")
        self.assertEqual((j.salary_min, j.salary_max, j.currency), (40000, 55000, "EUR"))


if __name__ == "__main__":
    unittest.main()
