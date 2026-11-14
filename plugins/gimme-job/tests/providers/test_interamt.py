import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """<table><tr class="ia-e-table__row"><td data-field="Stellenbezeichnung">Softwareentwickler (m/w/d)</td>
<td data-field="StellenangebotId"><span>123456</span></td><td data-field="Behoerde">Stadt Musterstadt</td>
<td data-field="Dienstort">Vollzeit</td><td data-field="PLZOrte">12345 Musterstadt</td>
<td data-field="Von">05.10.2026</td><td data-field="Bewerbungsfrist">31.10.2026</td></tr></table>"""


class TestInteramt(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("interamt")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://interamt.de/koop/app/"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"interamt.de/koop/app/": HTML})
        jobs = self.p.fetch(Target(), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://interamt.de/koop/app/stelle?id=123456")
        self.assertEqual(j.company, "Stadt Musterstadt")
        self.assertEqual(j.posted_at, "2026-10-05")
        self.assertEqual(j.closes_at, "2026-10-31")
        self.assertEqual(j.source, "interamt")


if __name__ == "__main__":
    unittest.main()
