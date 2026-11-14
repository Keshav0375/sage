import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """<div><a href="https://karriere.heckler-koch.com/jobposting/abc123def" class="x"><h3>Entwickler (m/w/d) &amp; Test</h3></a>
<a href="https://karriere.heckler-koch.com/jobposting/abc123def"><h3>dup</h3></a>
<a href="https://karriere.heckler-koch.com/jobposting/zz9"><h3>Konstrukteur</h3></a></div>"""


class TestHecklerKoch(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("hecklerkoch")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://www.heckler-koch.com/de/Karriere/Stellenangebote"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"heckler-koch.com/de/Karriere/Stellenangebote": HTML})
        jobs = self.p.fetch(Target(company="Heckler & Koch"), ctx)
        self.assertEqual([j.title for j in jobs], ["Entwickler (m/w/d) & Test", "Konstrukteur"])
        self.assertEqual(jobs[0].url, "https://karriere.heckler-koch.com/jobposting/abc123def")
        self.assertEqual(jobs[0].source, "hecklerkoch")


if __name__ == "__main__":
    unittest.main()
