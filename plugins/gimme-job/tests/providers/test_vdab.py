import os
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import ProviderError, Target

KEY = "b277002f-e1fa-4fc5-868a-fdab633c3851"
FIXTURE = {"resultaten": [{
    "id": {"id": "abcd-1234"}, "vacaturefunctie": {"naam": "Softwareontwikkelaar"},
    "vacatureBedrijfsnaam": "Acme NV", "tewerkstellingsLocatieRegioOfAdres": "Gent",
    "eerstePublicatieDatum": "2026-11-05T00:00:00",
}]}


class TestVdab(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("vdab")

    def test_fetch_with_option_key(self):
        ctx = ctx_with({"vdab.be/rest/vindeenjob": FIXTURE})
        jobs = self.p.fetch(Target(query="software", options={"vej_key": KEY}), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://www.vdab.be/vindeenjob/vacatures/abcd-1234")
        self.assertEqual((j.title, j.company, j.location), ("Softwareontwikkelaar", "Acme NV", "Gent"))
        self.assertEqual(ctx.http.transport.calls[-1][0], "POST")

    def test_key_derived_from_bundle(self):
        bundle = "https://www.vdab.be/webapps/vindeenjob/main-ABC123.js"
        ctx = ctx_with({
            "vindeenjob/vacatures": f'<script src="{bundle}"></script>',
            "main-ABC123.js": f'x("vej-key-monitor","{KEY}")',
            "vdab.be/rest/vindeenjob": FIXTURE,
        })
        os.environ.pop("GIMME_JOB_VDAB_KEY", None)
        jobs = self.p.fetch(Target(query="software"), ctx)
        self.assertEqual(len(jobs), 1)

    def test_no_key(self):
        with self.assertRaises(ProviderError):
            self.p.fetch(Target(query="x"), ctx_with({"vindeenjob/vacatures": "<html></html>"}))


if __name__ == "__main__":
    unittest.main()
