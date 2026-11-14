import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target


def hit(f):
    def meta(n, v):
        return "" if v is None else f'<Meta name="{n}"><MetaString name="value">{v}</MetaString></Meta>'
    return ('<Hit did="d" url="x"><metas>' + meta("content_title", f.get("title")) + meta("content_cta_1_url", f.get("cta1"))
            + meta("content_categories", f.get("cats")) + meta("card_id", f.get("id"))
            + meta("content_start_datetime", f.get("start")) + meta("card_update_timestamp", f.get("update"))
            + "</metas></Hit>")


XML = ('<Answer nhits="2"><hits>'
       + hit({"id": "111", "title": "Software Engineer &amp; Data", "cta1": "https://www.3ds.com/careers/jobs/x-111?a=1&amp;b=2",
              "cats": "Category/R&amp;D Type/Regular Country/Germany City/Germany, Munich Products/CATIA", "update": "2026/07/03 18:22:13"})
       + hit({"id": "222", "title": "Data Scientist", "cta1": "https://www.3ds.com/careers/jobs/y-222",
              "cats": "Category/Sales Country/France City/France, Vélizy-Villacoublay", "start": "2026/06/01 09:00:00"})
       + hit({"id": "333", "title": "Evil", "cta1": "https://evil.example.com/x"})
       + "</hits></Answer>")


class TestDassault(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("dassault")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://www.3ds.com/careers"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"3ds.com/apisearch/card_search_api": XML})
        jobs = self.p.fetch(Target(), ctx)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0].title, "Software Engineer & Data")
        self.assertEqual(jobs[0].url, "https://www.3ds.com/careers/jobs/x-111?a=1&b=2")
        self.assertEqual(jobs[0].location, "Germany, Munich")
        self.assertTrue(jobs[0].posted_at.startswith("2026-07-03"))
        self.assertTrue(jobs[1].posted_at.startswith("2026-06-01"))
        self.assertEqual(jobs[0].company, "Dassault Systèmes")
        self.assertEqual(jobs[0].source, "dassault")


if __name__ == "__main__":
    unittest.main()
