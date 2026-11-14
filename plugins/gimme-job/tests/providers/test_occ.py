import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """<html><body>
<div class="card-job-offer x" data-id='19876543'>
  <h2 class="title">Ingeniero de Automatizaci&oacute;n</h2>
  <div class="h-[21px] flex"><span>ACME Mexico</span></div>
  <div class="no-alter-loc-text"><span></span><p>Monterrey, Nuevo Le&oacute;n</p></div>
</div>
<div class="card-job-offer y" data-id='19876544'>
  <h2>Analista</h2>
  <div class="h-[21px]"><span>Empresa confidencial</span></div>
  <div class="no-alter-loc-text"><p>CDMX</p></div>
</div></body></html>"""


class TestOcc(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("occ")
        ctx = ctx_with({"occ.com.mx/empleos/de-automatizacion": HTML}, max_jobs=500)
        jobs = p.fetch(Target(query="automatización", options={"max_pages": 1}), ctx)
        self.assertEqual(len(jobs), 2)
        j = jobs[0]
        self.assertEqual(j.title, "Ingeniero de Automatización")
        self.assertEqual(j.company, "ACME Mexico")
        self.assertEqual(j.location, "Monterrey, Nuevo León")
        self.assertEqual(j.url, "https://www.occ.com.mx/empleo/oferta/19876543/")
        self.assertEqual(jobs[1].company, "")


if __name__ == "__main__":
    unittest.main()
