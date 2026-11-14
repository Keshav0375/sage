import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """<ul>
<li class="list-item"><a class="item-details-link" href="/careers/cityofx/jobs/4501234/police-officer">Police Officer</a>
<ul class="list-meta"><li>Springfield, IL</li><li>Full-Time</li></ul></li>
<li class="list-item"><a class="item-details-link" href="/careers/cityofx/jobs/4501235/clerk">Records Clerk</a>
<ul class="list-meta"><li>Springfield, IL</li></ul></li>
</ul>"""
EMPTY = '<div class="jobs-not-found-container">No jobs</div>'


class TestNeogov(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("neogov")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://www.governmentjobs.com/careers/cityofx").slug, "cityofx")
        self.assertIsNone(self.p.detect("https://www.governmentjobs.com/careers/home"))
        self.assertIsNone(self.p.detect("https://example.com/careers/cityofx"))

    def test_fetch(self):
        ctx = ctx_with({"page=1": HTML, "page=2": EMPTY})
        jobs = self.p.fetch(Target(company="City of X", careers_url="https://www.governmentjobs.com/careers/cityofx"), ctx)
        self.assertEqual([j.title for j in jobs], ["Police Officer", "Records Clerk"])
        self.assertEqual(jobs[0].url, "https://www.governmentjobs.com/careers/cityofx/jobs/4501234/police-officer")
        self.assertEqual(jobs[0].location, "Springfield, IL")
        self.assertEqual(jobs[0].source, "neogov")


if __name__ == "__main__":
    unittest.main()
