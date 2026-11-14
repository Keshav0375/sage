import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

ND = {"props": {"pageProps": {"serverState": {"initialResults": {"jobs": {"results": [{"hits": [
    {"objectID": "77", "title": "Product Designer", "slug": "product-designer-acme-77", "startup": "Acme Labs",
     "location": {"name": "Lausanne"}, "created": 1762732800},
    {"slug": "x"},
]}]}}}}}}
HTML = '<html><script id="__NEXT_DATA__" type="application/json">' + json.dumps(ND) + "</script></html>"


class TestJoinUp(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("joinup")
        jobs = p.fetch(Target(), ctx_with({"joinup.ch/browse/jobs": HTML}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://joinup.ch/job/product-designer-acme-77")
        self.assertEqual((j.company, j.location), ("Acme Labs", "Lausanne"))
        self.assertTrue(j.posted_at.startswith("2025-11-10"))


if __name__ == "__main__":
    unittest.main()
