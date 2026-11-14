import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.getonbrd import PROVIDER

FIXTURE = {"data": [{"id": "senior-python-acme", "type": "job", "attributes": {
    "title": "Senior Python Developer", "remote": True, "countries": ["Chile"], "published_at": 1760000000,
    "company": {"data": {"id": "5", "attributes": {"name": "Acme"}}}},
    "links": {"public_url": "https://www.getonbrd.com/jobs/programming/senior-python-acme-santiago"}}]}


class TestGetOnBoard(unittest.TestCase):
    def test_fetch(self):
        ctx = ctx_with({"getonbrd.com/api/v0/categories/programming/jobs": FIXTURE})
        jobs = PROVIDER.fetch(Target(), ctx)
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.workplace), ("Senior Python Developer", "Acme", "Remote", "remote"))
        self.assertEqual(j.url, "https://www.getonbrd.com/jobs/programming/senior-python-acme-santiago")
        self.assertTrue(j.posted_at.startswith("2025-10"))

    def test_bad_category(self):
        from scripts.providers._base import ProviderError
        with self.assertRaises(ProviderError):
            PROVIDER.fetch(Target(options={"category": "Bad Slug!"}), ctx_with({}))


if __name__ == "__main__":
    unittest.main()
