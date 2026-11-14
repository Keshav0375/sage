import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

CARD = """<li class="row"><div class="iCIMS_JobCardItem"><a class="iCIMS_Anchor" href="https://careers-acme.icims.com/jobs/1234/data-analyst/job?in_iframe=1">
<h3>Data Analyst</h3></a><div class="header"><span class="field-label sr-only">Location : City</span><span>Toronto</span></div></div></li>"""


class TestIcims(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("icims")

    def test_detect(self):
        t = self.p.detect("https://careers-acme.icims.com/jobs/search?ss=1")
        self.assertEqual(t.slug, "careers-acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        ctx = ctx_with({"pr=0": CARD, "pr=1": "<html></html>"})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://careers-acme.icims.com/jobs/search"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.company, j.source), ("Data Analyst", "Toronto", "Acme", "icims"))
        self.assertEqual(j.url, "https://careers-acme.icims.com/jobs/1234/data-analyst/job")


if __name__ == "__main__":
    unittest.main()
