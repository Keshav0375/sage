import base64
import json
import shutil
import subprocess
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

URL = "https://hire-r1.mokahr.com/social-recruitment/acme/12345"
PLAIN = {"success": True, "data": {"jobs": [{
    "id": "uuid-1", "title": "数据工程师", "createdAt": "2026-10-01T08:00:00+08:00",
    "locations": [{"provinceName": "广东", "cityName": "深圳"}], "department": {"name": "数据部"},
    "commitment": "全职", "jobDescription": "<p>建设<b>数据平台</b></p>"}]}}


class TestMokaHr(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("mokahr")

    def test_detect(self):
        t = self.p.detect(URL + "#/jobs")
        self.assertEqual(t.slug, "acme")
        self.assertEqual(t.options["site_id"], 12345)
        self.assertIsNone(self.p.detect("https://example.com/social-recruitment/acme/1"))
        self.assertIsNone(self.p.detect("https://app.mokahr.com/other/acme/1"))

    def test_fetch_plain(self):
        ctx = ctx_with({"mokahr.com/api/outer/ats-apply/website/jobs/v2": PLAIN})
        jobs = self.p.fetch(self.p.detect(URL).__class__(company="Acme", careers_url=URL), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "数据工程师")
        self.assertEqual(j.url, URL + "#/job/uuid-1")
        self.assertEqual(j.location, "广东 深圳")
        self.assertIn("数据平台", j.description)
        self.assertEqual(j.source, "mokahr")

    @unittest.skipUnless(shutil.which("openssl"), "openssl CLI not available")
    def test_fetch_encrypted(self):
        key = b"0123456789abcdef"
        iv = b"de7c21ed8d6f50fe"
        enc = subprocess.run(["openssl", "enc", "-aes-128-cbc", "-K", key.hex(), "-iv", iv.hex()],
                             input=json.dumps(PLAIN).encode(), capture_output=True, check=True).stdout
        env = {"data": base64.b64encode(enc).decode(), "necromancer": key.decode()}
        ctx = ctx_with({"app.mokahr.com/api/outer": env})
        u = "https://app.mokahr.com/social-recruitment/acme/12345"
        jobs = self.p.fetch(Target(company="Acme", careers_url=u), ctx)
        self.assertEqual(jobs[0].title, "数据工程师")
        self.assertEqual(jobs[0].url, u + "#/job/uuid-1")


if __name__ == "__main__":
    unittest.main()
