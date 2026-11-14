import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """<div class="matchElement" id="job_id_555">
  <a href="/de/job/555/Projektleiter?x=1&amp;y=2">Projektleiter (m/w/d)</a>
  <span class="location-view-item">Berlin</span><span class="location-view-item">Leipzig</span>
  <div class="matchValue date">10/15/2026</div>
</div>"""


class TestSoftgarden(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("softgarden")

    def test_detect(self):
        t = self.p.detect("https://acme.softgarden.io/de/")
        self.assertEqual(t.api_url, "https://acme.softgarden.io/de/widgets/jobs")
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"acme.softgarden.io/de/widgets/jobs": HTML})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://acme.softgarden.io/de/"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Projektleiter (m/w/d)")
        self.assertEqual(j.url, "https://acme.softgarden.io/de/job/555/Projektleiter?x=1&y=2")
        self.assertEqual(j.location, "Berlin / Leipzig")
        self.assertEqual(j.posted_at, "2026-10-15")
        self.assertEqual(j.source, "softgarden")


if __name__ == "__main__":
    unittest.main()
