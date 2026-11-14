import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target


def gql(url_body):
    import json
    ops = json.loads(url_body)
    if ops[0]["operationName"] == "JobBoardList":
        return [{"data": {"oatsExternalJobPostings": {"jobPostings": [
            {"extId": "abc123", "title": "Product Designer", "locations": [{"name": "New York, NY", "isRemote": False}, {"name": "Remote US", "isRemote": True}],
             "job": {"department": {"name": "Design"}, "locationType": "hybrid", "employmentType": "full_time"}}]}}}]
    return [{"data": {"oatsExternalJobPosting": {"extId": "abc123", "firstPublishedTsSec": 1762300800, "descriptionHtml": "<p>Design things.</p>"}}}]


class TestGem(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("gem")

    def test_detect(self):
        self.assertEqual(self.p.detect("https://jobs.gem.com/acme").slug, "acme")
        self.assertIsNone(self.p.detect("https://example.com/careers"))

    def test_fetch_graphql(self):
        from scripts.providers._http import Response
        import json
        ctx = ctx_with({})
        def handler(method, url, headers, data, timeout):
            return Response(200, json.dumps(gql(data.decode())).encode(), {}, url)
        ctx.http.transport.request = handler
        jobs = self.p.fetch(Target(company="Acme", slug="acme"), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.url, j.department, j.workplace, j.source),
                         ("Product Designer", "https://jobs.gem.com/acme/abc123", "Design", "hybrid", "gem"))
        self.assertEqual(j.location, "New York, NY | Remote US · Remote")
        self.assertIn("Design things", j.description)
        self.assertTrue(j.posted_at.startswith("2025-11-05"))

    def test_fetch_rest(self):
        feed = {"job_posts": [{"id": 1, "title": "SRE", "absolute_url": "https://jobs.gem.com/acme/xyz", "content_plain": "Run it.",
                               "first_published_at": "2026-11-01T00:00:00Z", "location": {"name": "Austin, TX"}}]}
        ctx = ctx_with({"api.gem.com/job_board/v0/acme/job_posts": feed})
        jobs = self.p.fetch(Target(company="Acme", slug="acme", api_url="https://api.gem.com/job_board/v0/acme/job_posts"), ctx)
        self.assertEqual((jobs[0].title, jobs[0].location), ("SRE", "Austin, TX"))


if __name__ == "__main__":
    unittest.main()
