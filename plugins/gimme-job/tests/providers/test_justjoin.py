import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.justjoin import PROVIDER

FIXTURE = {"data": [{
    "guid": "g-1", "slug": "acme-python-developer-warszawa", "title": "Python Developer", "companyName": "Acme",
    "workplaceType": "remote", "city": "Warszawa", "locations": [{"city": "Warszawa"}],
    "lastPublishedAt": "2026-10-22T09:00:00Z"}], "meta": {"next": {"cursor": None}}}


class TestJustJoin(unittest.TestCase):
    def test_fetch(self):
        jobs = PROVIDER.fetch(Target(), ctx_with({"justjoin.it/api/candidate-api/offers": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.workplace), ("Python Developer", "Acme", "Warszawa", "remote"))
        self.assertEqual(j.url, "https://justjoin.it/job-offer/acme-python-developer-warszawa")


if __name__ == "__main__":
    unittest.main()
