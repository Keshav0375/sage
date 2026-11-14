import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.magneto import PROVIDER

PAGE = '''<html><article class="card-jobs"><a href="/co/empleos/desarrollador-python-bogota-4521" title="x"><span>Desarrollador Python</span></a>
<h3>Acme SAS | Bogotá</h3><p>$ 5.000.000</p><p>Bogotá, D.C.</p></article>
<article class="card-jobs"><a href="/co/empleos/analista-777"><span>Analista</span></a><h3>Confidencial</h3><p>Cali</p></article></html>'''


class TestMagneto(unittest.TestCase):
    def test_fetch(self):
        ctx = ctx_with({"magneto365.com/co/empleos": PAGE})
        jobs = PROVIDER.fetch(Target(options={"max_pages": 1}), ctx)
        self.assertEqual(len(jobs), 2)
        a, b = jobs
        self.assertEqual((a.title, a.company, a.location), ("Desarrollador Python", "Acme SAS", "Bogotá, D.C."))
        self.assertEqual(a.url, "https://www.magneto365.com/co/empleos/desarrollador-python-bogota-4521")
        self.assertEqual((b.company, b.location), ("", "Cali"))


if __name__ == "__main__":
    unittest.main()
