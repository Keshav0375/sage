import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

def item(name, url):
    return '{"@type":"ListItem","position":1,"name":"%s","url":"%s"}' % (name, url)


def card(i, title, company, posted, mode, loc, pay=""):
    return f'''
<div><a href="/company/{company.lower()}" class="z-1"><span>{company}</span></a></div>
<h2><a href="/job/x/{i}" data-id="job-card-title" data-builtin-track-job-id="{i}">{title}</a></h2>
<div><i class="fa-regular fa-clock"></i>{posted}</span></div>
<div><div><i class="fa-regular fa-house-building"></i></div> <span class="a">{mode}</span></div>
<div><div><i class="fa-regular fa-location-dot"></i></div> <div><span class="b">{loc}</span></div></div>
{('<div><div><i class="fa-regular fa-sack-dollar"></i></div> <span class="c">' + pay + '</span></div>') if pay else ''}
'''


PAGE = ("<html><body>" + card(101, "Backend Engineer", "Acme", "Yesterday", "Hybrid", "Seattle, WA, USA", "170K-230K Annually")
        + card(102, "Platform Engineer", "Globex", "2 Days Ago", "Remote", "United States")
        + "<script>{\"itemListElement\":[" + ",".join([
            item("Backend Engineer", "https://builtin.com/job/backend-engineer/101"),
            item("Platform Engineer", "https://builtin.com/job/platform-engineer/102"),
            '{"@type":"ListItem","position":3,"name":"Broken}']) + "]}</script></body></html>")


class TestBuiltIn(unittest.TestCase):
    def setUp(self):
        self.p = _registry.get("builtin")

    def test_detect_none(self):
        self.assertIsNone(self.p.detect("https://builtin.com/jobs"))

    def test_fetch(self):
        ctx = ctx_with({"builtin.com/jobs?search=python&page=1": PAGE})
        jobs = self.p.fetch(Target(query="python"), ctx)
        self.assertEqual(len(jobs), 2)
        a, b = jobs
        self.assertEqual((a.title, a.company, a.location, a.source), ("Backend Engineer", "Acme", "Hybrid · Seattle, WA, USA", "builtin"))
        self.assertEqual((a.salary_min, a.salary_max, a.workplace), (170000, 230000, "hybrid"))
        self.assertEqual((b.company, b.workplace), ("Globex", "remote"))
        self.assertTrue(a.posted_at)

    def test_needs_query(self):
        from scripts.providers._base import ProviderError
        with self.assertRaises(ProviderError):
            self.p.fetch(Target(), ctx_with({}))


if __name__ == "__main__":
    unittest.main()

