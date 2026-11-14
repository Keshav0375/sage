import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"hits": {"hits": [{"_id": "abc", "_source": {
    "title": "Data Scientist", "url": "https://careers.ibm.com/job/21000001/data-scientist/",
    "field_keyword_19": "Toronto, CA", "field_keyword_17": "Hybrid", "field_keyword_05": "Canada", "dcdate": "2026-11-04"}}]}}


class TestIbm(unittest.TestCase):
    def test_fetch(self):
        ctx = ctx_with({"www-api.ibm.com/search/api/v2": FIXTURE})
        jobs = _registry.get("ibm").fetch(Target(options={"ibm": {"country": "Canada"}}), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.workplace), ("Data Scientist", "IBM", "Toronto, CA · Hybrid", "hybrid"))
        self.assertTrue(j.posted_at.startswith("2026-11-04"))
        body = json.loads(ctx.http.transport.calls[0][2])
        self.assertEqual(body["post_filter"]["bool"]["must"], [{"term": {"field_keyword_05": "Canada"}}])


if __name__ == "__main__":
    unittest.main()
