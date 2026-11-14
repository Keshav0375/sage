import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"success": True, "content": {"totalCount": 1, "datas": [{
    "id": 1234, "name": "后端开发工程师", "workLocations": ["杭州", "北京"], "categories": ["技术类"],
    "experience": {"from": 3, "to": 5}, "description": "负责服务开发", "requirement": "熟悉Java",
    "publishTime": 1760000000000}]}}


class TestAlibaba(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("alibaba")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://talent.alibaba.com/off-campus/position-list"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"talent.alibaba.com/position/search": FIXTURE})
        jobs = self.p.fetch(Target(company="阿里巴巴"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "后端开发工程师")
        self.assertEqual(j.url, "https://talent.alibaba.com/off-campus/position-detail?positionId=1234")
        self.assertEqual(j.locations, ["杭州", "北京"])
        self.assertEqual(j.source, "alibaba")
        self.assertIn("Java", j.description)


if __name__ == "__main__":
    unittest.main()
