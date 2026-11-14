import unittest

from tests.providers._helpers import ctx_with
from scripts.providers._base import Target
from scripts.providers.jobscz import PROVIDER

def card(i, title, status, company, loc):
    return ('<article\n  class="SearchResultCard" ><header><h2 data-test-ad-title="%s"><a data-jobad-id="%s" href="https://www.jobs.cz/rpd/%s/?x=1">%s</a></h2>'
            '<div data-test-ad-status="default" class="s">%s</div></header><footer><ul><li><span translate="no">%s</span></li>'
            '<li data-test="serp-locality"> %s </li></ul></footer></article>') % (title, i, i, title, status, company, loc)


PAGE = "<html><body><h1>Našli jsme 1 nabídku</h1>" + card("2000123", "Python vývojář", "Přidáno dnes", "Acme s.r.o.", "Praha") + "</body></html>"


class TestJobsCz(unittest.TestCase):
    def test_fetch(self):
        jobs = PROVIDER.fetch(Target(query="python"), ctx_with({"jobs.cz/prace/": PAGE}))
        self.assertEqual(len(jobs), 1)
        j = jobs[0]
        self.assertEqual((j.title, j.company, j.location), ("Python vývojář", "Acme s.r.o.", "Praha"))
        self.assertEqual(j.url, "https://www.jobs.cz/rpd/2000123/")
        self.assertTrue(j.posted_at)

    def test_empty(self):
        html = "<html>Nenašli jsme žádné nabídky</html>"
        self.assertEqual(PROVIDER.fetch(Target(query="zzz"), ctx_with({"jobs.cz/prace/": html})), [])


if __name__ == "__main__":
    unittest.main()
