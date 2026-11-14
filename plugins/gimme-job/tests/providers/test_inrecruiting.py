import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """<html><input id="url-for-announces" value="https://acme.intervieweb.it/app.php?x=1">
<script>var cfg = {'section': 'career_it'};</script>
<a href="https://acme.intervieweb.it/jobs/sviluppatore-backend-123/it/"><h3>Sviluppatore Backend</h3></a>
<span><i class="mi-location_on"></i><span class="sr-only">Sede</span>Milano</span>
</html>"""


class TestInRecruiting(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("inrecruiting")

    def test_detect(self):
        t = self.p.detect("https://acme.intervieweb.it/en/career")
        self.assertEqual(t.api_url, "https://acme.intervieweb.it/en/career")
        self.assertIsNone(self.p.detect("https://inrecruiting.intervieweb.it/"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"acme.intervieweb.it/it/career": HTML})
        jobs = self.p.fetch(Target(company="Acme", careers_url="https://acme.intervieweb.it/"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Sviluppatore Backend")
        self.assertEqual(j.url, "https://acme.intervieweb.it/jobs/sviluppatore-backend-123/it/")
        self.assertEqual(j.location, "Milano")
        self.assertEqual(j.source, "inrecruiting")


if __name__ == "__main__":
    unittest.main()
