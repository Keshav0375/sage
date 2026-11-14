import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

URL = "https://acme.taleo.net/careersection/ex/jobsearch.ftl?lang=en"
SHELL = """<html><script>var x = {"portal": "101430233"};</script>
<table id="jobs"><thead><tr><th>Requisition Title</th><th>Location</th><th>Posting Date</th></tr></thead></table></html>"""
RESP = {"requisitionList": [{"contestNo": "R-1001", "column": ["Payroll Analyst", "[\"Ottawa, ON\",\"Remote\"]", "Nov 3, 2026"]}],
        "pagingData": {"totalCount": "1"}}


class TestTaleo(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("taleo")

    def test_detect(self):
        self.assertEqual(self.p.detect(URL).slug, "ex")
        self.assertIsNone(self.p.detect("https://tre.taleo.net/careersection/ex/jobsearch.ftl"))
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"jobboard/searchjobs": RESP, "jobsearch.ftl": SHELL})
        jobs = self.p.fetch(Target(company="Acme", careers_url=URL), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.source), ("Payroll Analyst", "Ottawa, ON; Remote", "taleo"))
        self.assertEqual(j.url, "https://acme.taleo.net/careersection/ex/jobdetail.ftl?job=R-1001&lang=en")
        self.assertTrue(j.posted_at.startswith("2026-11-03"))


if __name__ == "__main__":
    unittest.main()
