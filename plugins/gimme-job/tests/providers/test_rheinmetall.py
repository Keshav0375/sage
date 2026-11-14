import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """<div class="list"><div class="flex gap-0.5 group">
<a href="/en/job/Software_Engineer_(m/w/d)/12345"><div class="md:text-xl font-bold">Software Engineer &amp; Co</div></a>
<div class="flex flex-wrap mr-6">Rheinmetall Electronics | Bremen</div></div>
<div class="flex gap-0.5 group"><a href="/en/job/Controller/67890"><div class="md:text-xl x">Controller</div></a></div></div>"""


class TestRheinmetall(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("rheinmetall")

    def test_detect(self):
        self.assertIsNotNone(self.p.detect("https://www.rheinmetall.com/en/career/vacancies"))
        self.assertIsNone(self.p.detect("https://example.com/"))

    def test_fetch(self):
        ctx = ctx_with({"rheinmetall.com/en/career/vacancies": HTML})
        jobs = self.p.fetch(Target(company="Rheinmetall"), ctx)
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0].title, "Software Engineer & Co")
        self.assertEqual(jobs[0].url, "https://www.rheinmetall.com/en/job/Software_Engineer_(m/w/d)/12345")
        self.assertEqual(jobs[0].location, "Bremen")
        self.assertEqual(jobs[0].source, "rheinmetall")


if __name__ == "__main__":
    unittest.main()
