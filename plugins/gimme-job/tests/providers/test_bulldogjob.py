import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.bulldogjob import PROVIDER

import json

DATA = {"props": {"pageProps": {"totalCount": 1, "jobs": [{
    "id": "acme-senior-python-developer-warszawa", "position": "Senior Python Developer", "city": "Warszawa",
    "remote": True, "locale": "en", "company": {"name": "Acme Sp. z o.o."}}]}}}
HTML = '<html><script id="__NEXT_DATA__" type="application/json">%s</script></html>' % json.dumps(DATA)


class TestBulldogjob(unittest.TestCase):
    def test_fetch(self):
        jobs = PROVIDER.fetch(Target(), ctx_with({"bulldogjob.pl/companies/jobs/s/page,1": HTML}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location, j.workplace), ("Senior Python Developer", "Acme Sp. z o.o.", "Warszawa", "remote"))
        self.assertEqual(j.url, "https://bulldogjob.pl/companies/jobs/acme-senior-python-developer-warszawa")
        self.assertEqual(j.source, "bulldogjob")


if __name__ == "__main__":
    unittest.main()
