import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """<script type="application/ld+json">{"itemListElement":[
{"@type":"ListItem","position":1,"url": "https://www.bwi.de/karriere/stellenangebote/job/security-analyst-m-w-d-11111"},
{"@type":"ListItem","position":2,"url": "https://www.bwi.de/karriere/stellenangebote/job/consultant-cloud-22222"},
{"@type":"ListItem","position":3,"url": "https://www.bwi.de/karriere/stellenangebote/job/security-analyst-m-w-d-11111"}]}</script>"""


class TestBwi(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("bwi")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://www.bwi.de/karriere"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"bwi.de/karriere/stellenangebote": HTML})
        jobs = self.p.fetch(Target(company="BWI"), ctx)
        self.assertEqual([j.title for j in jobs], ["Security Analyst (m/w/d)", "Consultant Cloud"])
        self.assertEqual(jobs[0].url, "https://www.bwi.de/karriere/stellenangebote/job/security-analyst-m-w-d-11111")
        self.assertEqual(jobs[0].source, "bwi")


if __name__ == "__main__":
    unittest.main()
