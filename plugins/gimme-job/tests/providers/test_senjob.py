import unittest

from tests.providers._helpers import ctx_with
from scripts.providers import _registry
from scripts.providers._base import Target

HTML = """<table>
<tr style="height:70px;"><td>
  <a href="https://senjob.com/jobseekers/developpeur-fullstack_e_163401.html" style="font-size:18px;">
    D&eacute;veloppeur Fullstack
  </a></td></tr>
<tr><td><a href="https://senjob.com/jobseekers/developpeur-fullstack_e_163401.html">&nbsp;</a>
  Dakar <span style='color:#999;'> Publi&eacute;: </span><span style="display:none;">2026-08-14</span>14&nbsp;Aou.</td></tr>
<tr><td><a href="https://senjob.com/jobseekers/software-and-data-engineer_e_163402.html">Software and Data Engineer</a></td>
<td>Thies <span> Publi&eacute;: </span><span style="display:none;">2026-08-12</span>12 Aou.</td></tr>
</table>"""


class TestSenjob(unittest.TestCase):
    def test_fetch(self):
        p = _registry.get("senjob")
        jobs = p.fetch(Target(options={"max_pages": 1}), ctx_with({"senjob.com/offres-d-emploi.php": HTML}))
        self.assertEqual(len(jobs), 2)
        self.assertEqual(jobs[0].title, "Développeur Fullstack")
        self.assertTrue(jobs[0].posted_at.startswith("2026-08-14"))
        self.assertEqual(jobs[1].title, "Software and Data Engineer")
        self.assertEqual(jobs[1].location, "Thies")
        self.assertEqual(jobs[1].source, "senjob")


if __name__ == "__main__":
    unittest.main()
