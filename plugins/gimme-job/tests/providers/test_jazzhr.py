import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

PAGE = """<ul class="list-group">
<li class="list-group-item"><h4 class="list-group-item-heading"><a href="https://acme.applytojob.com/apply/AbC123/Line-Cook?source=x">Line Cook</a></h4>
<ul class="list-inline"><li><i class="fa fa-map-marker"></i> Denver, CO</li></ul></li></ul>"""


class TestJazzHR(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("jazzhr")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://acme.applytojob.com/apply").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://acme.applytojob.com"), ctx_with({"acme.applytojob.com/apply": PAGE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.source), ("Line Cook", "Denver, CO", "jazzhr"))
        self.assertEqual(j.url, "https://acme.applytojob.com/apply/AbC123/Line-Cook")


if __name__ == "__main__":
    unittest.main()
