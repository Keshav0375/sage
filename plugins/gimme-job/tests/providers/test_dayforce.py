import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

SEARCH = {"jobPostings": [
    {"jobPostingId": 1001, "jobTitle": "Payroll Analyst &amp; Lead", "jobDescription": "<p>Run payroll.</p>",
     "postingStartTimestampUTC": "2026-11-02T15:00:00Z",
     "postingLocations": [{"formattedAddress": "Toronto, ON, CA"}, {"cityName": "Calgary", "stateCode": "AB", "isoCountryCode": "CA"}]},
    {"jobPostingId": "bad", "jobTitle": "Skipped"}],
    "offset": 0, "count": 2, "maxCount": 2}


class TestDayforce(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("dayforce")

    def test_detect(self):
        t = self.p.detect("https://jobs.dayforcehcm.com/en-US/acme/CANDIDATEPORTAL")
        self.assertEqual((t.slug, t.options["board"], t.options["culture"]), ("acme", "CANDIDATEPORTAL", "en-US"))
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"/api/auth/csrf": {"csrfToken": "tok"}, "/api/geo/acme/jobposting/search": SEARCH})
        t = self.p.detect("https://jobs.dayforcehcm.com/en-US/acme/CANDIDATEPORTAL")
        t.company = "Acme"
        jobs = self.p.fetch(t, ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.source), ("Payroll Analyst & Lead", "Acme", "dayforce"))
        self.assertEqual(j.url, "https://jobs.dayforcehcm.com/en-US/acme/CANDIDATEPORTAL/jobs/1001")
        self.assertEqual(j.locations, ["Toronto, ON, CA", "Calgary, AB, CA"])
        self.assertIn("payroll", j.description)


if __name__ == "__main__":
    unittest.main()

