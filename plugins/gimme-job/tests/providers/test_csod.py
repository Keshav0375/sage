import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

URL = "https://acme.csod.com/ux/ats/careersite/4/home?c=acme"
HOME = '<script>window.csod = {"token": "eyJhbGciOi.abc-DEF_1"};</script>'
RESP = {"data": {"totalCount": 1, "requisitions": [{"requisitionId": 321, "displayJobTitle": "Nurse &amp; Educator",
        "postingEffectiveDate": "11/04/2026", "locations": [{"city": "Columbus", "country": "US"}]}]}}


class TestCsod(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("csod")

    def test_detect(self):
        self.assertEqual(self.p.detect(URL).slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"/services/x/career-site/v1/search": RESP, "/ux/ats/careersite/4/home": HOME})
        jobs = self.p.fetch(Target(company="Acme", careers_url=URL), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.posted_at, j.source), ("Nurse & Educator", "Columbus, US", "2026-11-04", "csod"))
        self.assertEqual(j.url, "https://acme.csod.com/ux/ats/careersite/4/home/requisition/321?c=acme")


if __name__ == "__main__":
    unittest.main()
