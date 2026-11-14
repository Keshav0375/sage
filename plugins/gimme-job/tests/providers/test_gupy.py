import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.gupy import PROVIDER

FIXTURE = {"data": [
    {"id": 1, "name": "Desenvolvedor Backend", "careerPageName": "Acme Brasil", "jobUrl": "https://acme.gupy.io/jobs/1?jobBoardSource=gupy_portal",
     "city": "São Paulo", "state": "São Paulo", "country": "Brasil", "workplaceType": "hybrid",
     "publishedDate": "2026-10-20T10:00:00.000Z", "description": "Vaga"},
    {"id": 2, "name": "Analista", "careerPageName": "Empresa confidencial", "jobUrl": "https://x.gupy.io/jobs/2"},
]}


class TestGupy(unittest.TestCase):
    def test_fetch(self):
        jobs = PROVIDER.fetch(Target(query="backend"), ctx_with({"portal.gupy.io/api/job-search/jobs": FIXTURE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.workplace, j.country), ("Desenvolvedor Backend", "Acme Brasil", "hybrid", "BR"))
        self.assertEqual(j.location, "São Paulo, São Paulo, Brasil")

    def test_detect(self):
        self.assertIsNotNone(PROVIDER.detect("https://portal.gupy.io/job-search"))
        self.assertIsNone(PROVIDER.detect("https://example.com"))


if __name__ == "__main__":
    unittest.main()
