import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

PAGE = """<table><tbody id="search-results-content"><tr><td>
<a class="job-link" href="/100/acme/en/job/555123/lecturer-in-physics">Lecturer in Physics</a></td></tr></tbody></table>"""
URL = "https://careers.pageuppeople.com/100/acme/en/listing/"


class TestPageUp(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("pageup")

    def test_detect(self):
        self.assertEqual(self.p.detect(URL).slug, "100/acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch(self):
        jobs = self.p.fetch(Target(company="Acme Uni", careers_url=URL), ctx_with({"/100/acme/en/listing/": PAGE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.source), ("Lecturer in Physics", "Acme Uni", "pageup"))
        self.assertEqual(j.url, "https://careers.pageuppeople.com/100/acme/en/job/555123")


if __name__ == "__main__":
    unittest.main()
