import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

TILES = """<ul><li class="job-tile job-id-9001 x"><a class="jobTitle-link" href="/job/Berlin-Engineer-BE/9001/">Engineer</a>
<span data-url="/job/Berlin-Engineer-BE/9001/" ></span><div id="job-9001-section-city-value">Berlin</div></li></ul>"""
CSB = {"totalJobs": 1, "jobSearchResult": [{"response": {"id": 77, "unifiedStandardTitle": "Buyer", "unifiedUrlTitle": "Buyer",
       "jobLocationShort": ["Munich, DE,"], "unifiedStandardStart": "03.11.2026"}}]}


class TestSuccessFactors(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("successfactors")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://career5.successfactors.eu/career?company=acme"))
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch_tiles(self):
        ctx = ctx_with({"startrow=0": TILES, "startrow=": "<html></html>"})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://jobs.acme.com/search/"), ctx)
        self.assertEqual(len(jobs), 1)
        self.assertEqual((jobs[0].title, jobs[0].location, jobs[0].source), ("Engineer", "Berlin", "successfactors"))
        self.assertEqual(jobs[0].url, "https://jobs.acme.com/job/Berlin-Engineer-BE/9001/")

    def test_fetch_csb(self):
        ctx = ctx_with({"services/recruiting/v1/jobs": CSB, "/search/": "<html></html>"})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://jobs.acme.com/", options={"variant": "csb"}), ctx)
        self.assertEqual(jobs[0].title, "Buyer")
        self.assertEqual(jobs[0].location, "Munich, DE")
        self.assertEqual(jobs[0].posted_at, "2026-11-03")


if __name__ == "__main__":
    unittest.main()
