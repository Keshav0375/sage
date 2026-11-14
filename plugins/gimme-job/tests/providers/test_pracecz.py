import json
import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

PAYLOAD = '{"totalItems":1,"currentPageItems":' + json.dumps([{
    "advert": {"title": "Python vývojář", "language": "cs",
               "workLocation": {"type": "FULL_REMOTE", "places": [{"city": "Praha"}]},
               "salary": {"min": 60000, "max": 90000, "period": "MONTH", "currency": "czk", "displayMode": "RANGE"}},
    "metadata": {"advertId": 1234567, "publishedAt": "2026-11-09T10:00:00Z"},
    "company": {"publicName": "Acme s.r.o."},
    "extended": {"careerPage": {"url": "https://acme.jobs.cz/detail/1234567?x=1"}},
}]) + "}"
HTML = "<html><script>self.__next_f.push(" + json.dumps([1, PAYLOAD]) + ")</script></html>"


class TestPraceCz(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("pracecz")
        jobs = p.fetch(Target(query="python"), ctx_with({"prace.cz/nabidky/": HTML}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual(j.title, "Python vývojář")
        self.assertEqual(j.url, "https://acme.jobs.cz/detail/1234567")
        self.assertEqual((j.company, j.location, j.workplace), ("Acme s.r.o.", "Remote, Praha", "remote"))
        self.assertEqual((j.salary_min, j.currency, j.salary_period), (60000, "CZK", "month"))


if __name__ == "__main__":
    unittest.main()
