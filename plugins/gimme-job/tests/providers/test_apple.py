import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

DATA = {"loaderData": {"search": {"totalRecords": 1, "searchResults": [{
    "id": "200551234", "postingTitle": "Business Operations Specialist", "transformedPostingTitle": "business-operations-specialist",
    "postDateInGMT": "2026-11-05T00:00:00Z", "team": {"teamCode": "OPSC", "teamName": "Operations"},
    "locations": [{"name": "Cupertino", "countryName": "United States", "level": 2}]}]}}}
ESC = json.dumps(json.dumps(DATA))[1:-1]
HTML = f'<html><script>window.__staticRouterHydrationData = JSON.parse("{ESC}");</script></html>'


class TestApple(unittest.TestCase):
    def test_detect(self):
        p = _registry.get("apple")
        self.assertIsNotNone(p.detect("https://jobs.apple.com/en-us/search"))
        self.assertIsNone(p.detect("https://example.com"))

    def test_fetch(self):
        jobs = _registry.get("apple").fetch(Target(query="operations"), ctx_with({"jobs.apple.com/en-us/search": HTML}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Business Operations Specialist", "Apple", "Cupertino, United States"))
        self.assertEqual(j.url, "https://jobs.apple.com/en-us/details/200551234/business-operations-specialist?team=OPSC")

    def test_needs_query(self):
        from scripts.providers._base import ProviderError
        with self.assertRaises(ProviderError):
            _registry.get("apple").fetch(Target(), ctx_with({}))


if __name__ == "__main__":
    unittest.main()
