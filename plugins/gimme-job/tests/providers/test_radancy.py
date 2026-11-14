import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FRAG = {"results": """<section data-total-results="1" data-total-pages="1"><ul>
<li class="search-results-list__item"><a class="search-results-list__job-link" data-job-id="88001" href="/job/austin/store-manager/1234/88001">
<h2>Store Manager</h2></a><span class="search-results-list__job-info--location"><span>Austin, Texas</span></span></li></ul></section>"""}


class TestRadancy(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("radancy")
        ctx = ctx_with({"/en/search-jobs/results": FRAG})
        jobs = p.fetch(Target(company="Acme", careers_url="https://jobs.acme.com/en/search-jobs"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.location, j.source), ("Store Manager", "Austin, Texas", "radancy"))
        self.assertEqual(j.url, "https://jobs.acme.com/job/austin/store-manager/1234/88001")

    def test_detect_is_none(self):
        self.assertIsNone(_registry.get("radancy").detect("https://jobs.acme.com/en/search-jobs"))


if __name__ == "__main__":
    unittest.main()
