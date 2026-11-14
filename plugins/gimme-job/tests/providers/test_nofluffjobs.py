import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"totalPages": 1, "postings": [{
    "id": "ABC123", "title": "Senior Python Developer", "name": "Acme Sp. z o.o.",
    "url": "senior-python-developer-acme-warszawa-abc123", "posted": 1762732800000,
    "fullyRemote": True,
    "location": {"places": [{"city": "Warszawa", "country": {"name": "Poland"}}, {"province": "Mazowieckie"}]},
    "salary": {"from": 20000, "to": 28000, "currency": "PLN"},
}]}


class TestNoFluffJobs(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("nofluffjobs")
        jobs = p.fetch(Target(query="python"), ctx_with({"nofluffjobs.com/api/search/posting": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://nofluffjobs.com/pl/job/senior-python-developer-acme-warszawa-abc123")
        self.assertEqual(j.company, "Acme Sp. z o.o.")
        self.assertEqual(j.location, "Remote, Warszawa, Mazowieckie")
        self.assertEqual(j.workplace, "remote")
        self.assertEqual(j.source, "nofluffjobs")


if __name__ == "__main__":
    unittest.main()
