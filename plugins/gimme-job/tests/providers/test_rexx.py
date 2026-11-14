import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """<html><div id="joboffers">
<article class="joboffer_container">
  <a href="/stellenangebote/data-engineer-m-w-d-j1234.html">Data Engineer (m/w/d)</a>
  <span class="job_standort">M&uuml;nchen</span>
</article>
<article class="joboffer_container">
  <a href="https://jobs.acme.de/stellenangebote/buchhalter-j5678.html">Buchhalter</a>
  <div class="joboffer_informations">Vollzeit</div><div class="joboffer_informations">Hamburg</div>
</article>
</div></html>"""


class TestRexx(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("rexx")

    def test_detect_none_for_branded(self):
        self.assertIsNone(self.p.detect("https://jobs.acme.de/stellenangebote.html"))

    def test_fetch(self):
        ctx = ctx_with({"jobs.acme.de/stellenangebote.html": HTML})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://jobs.acme.de/"), ctx)
        self.assertEqual([j.title for j in jobs], ["Data Engineer (m/w/d)", "Buchhalter"])
        self.assertEqual(jobs[0].url, "https://jobs.acme.de/stellenangebote/data-engineer-m-w-d-j1234.html")
        self.assertEqual(jobs[0].location, "München")
        self.assertEqual(jobs[1].location, "Hamburg")
        self.assertEqual(jobs[0].source, "rexx")


if __name__ == "__main__":
    unittest.main()
