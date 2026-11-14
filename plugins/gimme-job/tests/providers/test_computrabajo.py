import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.computrabajo import PROVIDER

PAGE = '''<html><article class="box_offer" data-id='ABC123'><h2><a class="fc_base" href="/ofertas-de-trabajo/oferta-de-trabajo-de-desarrollador-python-en-bogota-ABC123#lc">Desarrollador Python</a></h2><p><a class="fc_base t_ellipsis offer-grid-article-company-url" href="/empresas/x">Acme SAS</a></p><p class="fs16 fc_base mt5"><span class="mr10">Bogotá, D.C.</span></p></article></html>'''


class TestComputrabajo(unittest.TestCase):
    def test_fetch(self):
        ctx = ctx_with({"co.computrabajo.com/trabajo-de-python": PAGE})
        jobs = PROVIDER.fetch(Target(query="python", options={"country": "co", "max_pages": 1}), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Desarrollador Python", "Acme SAS", "Bogotá, D.C."))
        self.assertEqual(j.url, "https://co.computrabajo.com/ofertas-de-trabajo/oferta-de-trabajo-de-desarrollador-python-en-bogota-ABC123")

    def test_rejects_foreign_host(self):
        from scripts.providers._base import ProviderError
        with self.assertRaises(ProviderError):
            PROVIDER.fetch(Target(careers_url="https://evil.example.com/x"), ctx_with({}))


if __name__ == "__main__":
    unittest.main()
