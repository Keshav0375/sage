import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

PAGE_ID = "0a1b2c3d-4e5f-4a6b-8c7d-9e0f1a2b3c4d"
CHILD = "11111111-2222-4333-8444-555555555555"
DB_ID = "22222222-3333-4444-8555-666666666666"
ROW = "33333333-4444-4555-8666-777777777777"
URL = "https://acme.notion.site/Careers-0a1b2c3d4e5f4a6b8c7d9e0f1a2b3c4d"


def blk(**kw):
    return {"value": {"value": kw, "role": "reader"}}


PAGE_CHUNK = {"recordMap": {"block": {
    PAGE_ID: blk(id=PAGE_ID, type="page", content=[CHILD]),
    CHILD: blk(id=CHILD, type="page", alive=True, properties={"title": [["Staff Engineer"]]}, created_time=1793000000000)}}}

DB_CHUNK = {"recordMap": {"block": {
    PAGE_ID: blk(id=PAGE_ID, type="collection_view_page", collection_id="col1", view_ids=["v1"], space_id="sp1")},
    "collection_view": {"v1": blk(id="v1", query2={"filter": {"operator": "and", "filters": []}})}}}
DB_ROWS = {"result": {"reducerResults": {"collection_group_results": {"blockIds": [ROW]}}},
           "recordMap": {"block": {ROW: blk(id=ROW, type="page", properties={"title": [["Designer"]], "loc": [["Remote,NYC"]]}, created_time=1793000000000)},
                         "collection": {"col1": blk(schema={"loc": {"name": "Location", "type": "multi_select"}})}}}


class TestNotion(unittest.TestCase):
    def test_detect(self):
        p = _registry.get("notion")
        t = p.detect(URL + "?v=aaaaaaaabbbbccccddddeeeeeeeeeeee")
        self.assertIsNotNone(t)
        self.assertTrue(t.api_url.startswith("https://acme.notion.site/"))
        self.assertIsNone(p.detect("https://www.notion.so/Careers-0a1b2c3d4e5f4a6b8c7d9e0f1a2b3c4d"))
        self.assertIsNone(p.detect("https://example.com/careers"))

    def test_plain_page(self):
        jobs = _registry.get("notion").fetch(Target(company="Acme", careers_url=URL), ctx_with({"loadPageChunk": PAGE_CHUNK}))
        self.assertEqual(len(jobs), 1)
        self.assertEqual((jobs[0].title, jobs[0].company), ("Staff Engineer", "Acme"))
        self.assertEqual(jobs[0].url, "https://acme.notion.site/" + CHILD.replace("-", ""))

    def test_database(self):
        ctx = ctx_with({"loadPageChunk": DB_CHUNK, "queryCollection": DB_ROWS})
        jobs = _registry.get("notion").fetch(Target(company="Acme", careers_url=URL), ctx)
        self.assertEqual(len(jobs), 1)
        self.assertEqual((jobs[0].title, jobs[0].location), ("Designer", "Remote · NYC"))


if __name__ == "__main__":
    unittest.main()
