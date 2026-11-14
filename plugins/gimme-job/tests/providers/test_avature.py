import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

PAGE = """<section><article class="article article--result">
<h3 class="article__header__text__title"><a href="/careers/JobDetail/Network-Engineer/12345">Network Engineer</a></h3>
<span class="list-item-location">Madrid, Spain</span><span>Posted 5-Nov-2026</span></article></section>"""
URL = "https://acme.avature.net/careers/SearchJobs"


class TestAvature(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("avature")

    def test_detect(self):
        self.assertEqual(self.p.detect(URL).slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(company="Acme", careers_url=URL), ctx_with({"acme.avature.net/careers/SearchJobs": PAGE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.posted_at, j.source), ("Network Engineer", "Madrid, Spain", "2026-11-05", "avature"))
        self.assertEqual(j.url, "https://acme.avature.net/careers/JobDetail/Network-Engineer/12345")


if __name__ == "__main__":
    unittest.main()
