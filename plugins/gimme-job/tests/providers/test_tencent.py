import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"Data": {"Count": 1, "Posts": [{
    "PostId": "1999", "RecruitPostName": "后台开发工程师", "CountryName": "中国", "LocationName": "深圳",
    "BGName": "WXG", "CategoryName": "技术", "Responsibility": "负责后台",
    "PostURL": "http://careers.tencent.com/jobdesc.html?postId=1999", "LastUpdateTime": "2026年06月23日"}]}}


class TestTencent(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("tencent")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://careers.tencent.com/home.html"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"careers.tencent.com/tencentcareer/api/post/Query": FIXTURE})
        jobs = self.p.fetch(Target(), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "后台开发工程师")
        self.assertEqual(j.location, "中国-深圳")
        self.assertEqual(j.posted_at, "2026-06-23")
        self.assertEqual(j.department, "WXG")
        self.assertEqual(j.source, "tencent")


if __name__ == "__main__":
    unittest.main()
