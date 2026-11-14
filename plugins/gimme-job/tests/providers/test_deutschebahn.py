import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """<div class="result-count" data-count="1"></div>
<a class="m-search-hit m-search-hit--x" href="/job-invite/123/?jobId=123" data-job-id="123">
<span class="m-search-hit__title-text">Lokf&uuml;hrer (w/m/d) &amp; Co</span>
<ul><li><i aria-label="Arbeitsort"></i> Berlin </li></ul></a>"""


class TestDeutscheBahn(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("deutschebahn")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://db.jobs/service/search/de-de/5441588"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"db.jobs/service/search/de-de/5441588": HTML})
        jobs = self.p.fetch(Target(company="Deutsche Bahn", careers_url="https://db.jobs/"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Lokführer (w/m/d) & Co")
        self.assertEqual(j.url, "https://db.jobs/job-invite/123/?jobId=123")
        self.assertEqual(j.location, "Berlin")
        self.assertEqual(j.source, "deutschebahn")


if __name__ == "__main__":
    unittest.main()
