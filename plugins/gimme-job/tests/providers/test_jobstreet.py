import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.jobstreet import PROVIDER

FIXTURE = {"totalCount": 1, "data": [{
    "id": "81234567", "title": "Software Engineer", "advertiser": {"id": "1", "description": "PT Acme Indonesia"},
    "locations": [{"label": "Jakarta Raya", "countryCode": "ID"}], "listingDate": "2026-10-21T02:00:00Z", "workTypes": ["Full time"]}]}


class TestJobStreet(unittest.TestCase):
    def test_fetch(self):
        ctx = ctx_with({"id.jobstreet.com/api/jobsearch/v5/search": FIXTURE})
        jobs = PROVIDER.fetch(Target(query="engineer", location="Jakarta"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Software Engineer", "PT Acme Indonesia", "Jakarta Raya"))
        self.assertEqual(j.url, "https://id.jobstreet.com/id/job/81234567")
        self.assertTrue(j.posted_at.startswith("2026-10-21"))


if __name__ == "__main__":
    unittest.main()
