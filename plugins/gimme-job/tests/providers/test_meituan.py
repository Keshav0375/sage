import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"data": {"page": {"totalCount": 1}, "list": [{
    "name": "算法工程师", "jobUnionId": "9988", "cityList": [{"name": "北京市"}, {"name": "上海市"}],
    "department": [{"name": "基础研发"}], "jobDuty": "负责算法", "jobRequirement": "熟悉ML",
    "refreshTime": 1760000000000}]}}


class TestMeituan(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("meituan")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://zhaopin.meituan.com/web/position"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"zhaopin.meituan.com/api/official/job/getJobList": FIXTURE})
        jobs = self.p.fetch(Target(), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://zhaopin.meituan.com/web/position/detail?jobUnionId=9988")
        self.assertEqual(j.locations, ["北京市", "上海市"])
        self.assertEqual(j.department, "基础研发")
        self.assertEqual(j.source, "meituan")


if __name__ == "__main__":
    unittest.main()
