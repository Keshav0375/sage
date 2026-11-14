import html
import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

RECORDS = [
    {"id": 555000001, "Posting_Title": "Sales Executive", "City": "Pune", "State": "MH", "Country": "India",
     "Remote_Job": False, "Date_Opened": "2026-10-01", "Job_Description": "<p>Sell <b>well</b></p>"},
    {"id": 555000002, "Posting_Title": "Closed Role", "Is_Locked": True},
]
PAGE = '<html><body><input type="hidden" id="jobs" value="%s"></body></html>' % html.escape(json.dumps(RECORDS), quote=True)


class TestZohoRecruit(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("zoho-recruit")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.zohorecruit.com/jobs/Careers").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/jobs/Careers"))

    def test_fetch(self):
        ctx = ctx_with({"acme.zohorecruit.com/jobs/Careers": PAGE})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://acme.zohorecruit.com/jobs/Careers"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Sales Executive")
        self.assertEqual(j.url, "https://acme.zohorecruit.com/jobs/Careers/555000001")
        self.assertEqual(j.location, "Pune, MH, India")
        self.assertIn("well", j.description)
        self.assertEqual(j.source, "zoho-recruit")


if __name__ == "__main__":
    unittest.main()
