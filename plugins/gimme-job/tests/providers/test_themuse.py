import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """<html><body><h1 class="sr-count">1,234 jobs</h1>
<article class="sr-tile" data-job-id="777"><h2 class="sr-tile__title"><a href="/jobs/acme/data-analyst-777">Data <!-- -->Analyst</a></h2>
<a href="/profiles/acme">Acme</a>
<div class="sr-tile__details"><p>Full-Time - New York, NY</p><p>Posted on Nov 10</p></div></article>
</body></html>"""


class TestTheMuse(unittest.TestCase):
    def test_fetch(self):
        ctx = ctx_with({"themuse.com/search": HTML}, max_jobs=1)
        jobs = _registry.get("themuse").fetch(Target(query="analyst", options={"remote": True}), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Data Analyst", "Acme", "New York, NY"))
        self.assertEqual(j.url, "https://www.themuse.com/jobs/acme/data-analyst-777")
        self.assertEqual(j.source_id, "777")
        self.assertRegex(j.posted_at, r"^\d{4}-11-10$")
        self.assertIn("q=analyst", ctx.http.transport.calls[0][1])

    def test_layout_change(self):
        from scripts.providers._base import ProviderError
        with self.assertRaises(ProviderError):
            _registry.get("themuse").fetch(Target(), ctx_with({"themuse.com/search": "<html></html>"}))


if __name__ == "__main__":
    unittest.main()
