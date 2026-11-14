import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

PAGE = '<html><script>window.serverInitialData = {"csrfToken":"abcdef123456","board":{"id":"acme-board","isParent":true}};</script></html>'
RESULT = {"jobs": [{"jobId": "j1", "title": "Data Scientist", "companyName": "PortCo", "url": "/jobs/j1",
                    "locations": ["Remote", "NYC"], "remote": True, "timeStamp": 1793000000000}], "total": 1, "meta": {}}


class TestConsider(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("consider")
        ctx = ctx_with({"/api-boards/search-jobs": RESULT, "vc.example.com/jobs": PAGE})
        jobs = p.fetch(Target(careers_url="https://vc.example.com/jobs"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.url), ("Data Scientist", "PortCo", "https://vc.example.com/jobs/j1"))
        self.assertEqual(j.location, "Remote, NYC")
        post = [c for c in ctx.http.transport.calls if c[0] == "POST"][0]
        self.assertEqual(json.loads(post[2])["board"]["id"], "acme-board")

    def test_rejects_private_host(self):
        from scripts.providers._base import ProviderError
        with self.assertRaises(ProviderError):
            _registry.get("consider").fetch(Target(careers_url="https://localhost/jobs"), ctx_with({}))


if __name__ == "__main__":
    unittest.main()
