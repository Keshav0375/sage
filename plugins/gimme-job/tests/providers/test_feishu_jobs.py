import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

FIXTURE = {"code": 0, "data": {"count": 1, "job_post_list": [{
    "id": "7001", "title": "后端工程师", "city_list": [{"name": "北京"}, {"name": "上海"}],
    "job_category": {"name": "研发"}, "description": "负责后端", "requirement": "熟悉Go",
    "publish_time": 1760000000000}]}}


class TestFeishuJobs(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("feishu-jobs")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://jobs.bytedance.com/experienced/position"))
        self.assertIsNotNone(self.p.detect("https://acme.jobs.feishu.cn/index"))
        self.assertIsNone(self.p.detect("https://example.com/"))
        self.assertIsNone(self.p.detect("http://jobs.bytedance.com/"))

    def test_fetch(self):
        ctx = ctx_with({"jobs.bytedance.com/api/v1/search/job/posts": FIXTURE})
        jobs = self.p.fetch(Target(company="ByteDance", careers_url="https://jobs.bytedance.com/experienced/position"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.url, "https://jobs.bytedance.com/experienced/position/7001/detail")
        self.assertEqual(j.locations, ["北京", "上海"])
        self.assertEqual(j.department, "研发")
        self.assertEqual(j.source, "feishu-jobs")

    def test_tenant_url_shape(self):
        ctx = ctx_with({"acme.jobs.feishu.cn/api/v1/search/job/posts": FIXTURE})
        jobs = self.p.fetch(Target(careers_url="https://acme.jobs.feishu.cn/index"), ctx)
        self.assertEqual(jobs[0].url, "https://acme.jobs.feishu.cn/index/position/7001/detail")


if __name__ == "__main__":
    unittest.main()
