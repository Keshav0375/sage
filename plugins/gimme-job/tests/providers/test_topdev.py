import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import ProviderError, Target

HTML = """<html><body>
<div class="rounded-xl border text-card-foreground shadow">
  <div><a href="/detail-jobs/senior-backend-engineer-acme-2012345?src=x">Senior Backend Engineer</a>
  <p class="company">Acme Vietnam</p></div>
  <div class="grid grid-cols-2 gap-2"><span><span>Ho Chi Minh</span></span><span>3 ngày trước</span></div>
</div>
<div class="rounded-xl text-card-foreground">
  <a href="https://evil.example/detail-jobs/x">Offsite</a><p>X</p>
</div></body></html>"""


class TestTopDev(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("topdev")

    def test_fetch(self):
        ctx = ctx_with({"topdev.vn/jobs/search": HTML})
        jobs = self.p.fetch(Target(query="backend", location="Ho Chi Minh", options={"max_pages": 1}), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://topdev.vn/detail-jobs/senior-backend-engineer-acme-2012345")
        self.assertEqual((j.title, j.company, j.location), ("Senior Backend Engineer", "Acme Vietnam", "Ho Chi Minh"))
        self.assertTrue(j.posted_at)
        self.assertIn("region_ids=79", ctx.http.transport.calls[-1][1])

    def test_challenge(self):
        with self.assertRaises(ProviderError):
            self.p.fetch(Target(query="x"), ctx_with({"topdev.vn/jobs/search": "<title>Just a moment...</title>"}))


if __name__ == "__main__":
    unittest.main()
