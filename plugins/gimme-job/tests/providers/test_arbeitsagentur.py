import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.arbeitsagentur import PROVIDER

FIXTURE = {"ergebnisliste": [{
    "referenznummer": "10001-1234567890-S", "stellenangebotsTitel": "Softwareentwickler (m/w/d)", "firma": "Beispiel AG",
    "homeofficeprozent": 100,
    "stellenlokationen": [{"adresse": {"ort": "Hamburg", "land": "Deutschland"}}]}]}


class TestArbeitsagentur(unittest.TestCase):
    def test_fetch(self):
        ctx = ctx_with({"jobsuche-service/pc/v6/jobs": FIXTURE})
        jobs = PROVIDER.fetch(Target(query="python", location="Hamburg"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.workplace), ("Softwareentwickler (m/w/d)", "Beispiel AG", "Hamburg", "remote"))
        self.assertTrue(j.url.startswith("https://www.arbeitsagentur.de/jobsuche/jobdetail/10001-1234567890-S"))
        self.assertIn("wo=Hamburg", ctx.http.transport.calls[0][1])

    def test_needs_keywords(self):
        from scripts.providers._base import ProviderError
        with self.assertRaises(ProviderError):
            PROVIDER.fetch(Target(), ctx_with({}))


if __name__ == "__main__":
    unittest.main()
