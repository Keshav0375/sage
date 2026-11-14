"""Core pipeline tests: knobs, dedupe/filters, rank, facts gate, lint, PII guard, Composio ingest, inbox, ledger, cards, versions."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

TMP = tempfile.mkdtemp(prefix="gimme-job-test-")
os.environ["GIMME_JOB_DATA"] = TMP
os.environ["GIMME_JOB_KNOBS"] = str(Path(TMP) / "knobs.toml")

from scripts import cards, common, composio_ingest, dedupe, facts, inbox_scan, knobs, ledger, lint_tex, rank, version  # noqa: E402
from scripts.providers import _registry  # noqa: E402

JD = ("Applied AI Engineer. Build LLM agents with tool calling, RAG over pgvector, evals with an LLM judge, MCP servers. "
      "Python, FastAPI, Kubernetes, Terraform. 2+ years of experience. Toronto, hybrid. $120,000 - $150,000 CAD per year.")


def job(i, **kw):
    d = {"id": f"j{i}", "title": "Applied AI Engineer", "url": f"https://example.com/jobs/{i}", "source": "greenhouse",
         "company": "Acme AI", "location": "Toronto, ON", "workplace": "hybrid", "description": JD,
         "posted_at": "2099-01-01T00:00:00+00:00", "salary_min": 120000, "salary_max": 150000, "currency": "CAD"}
    d.update(kw)
    return d


class TestKnobs(unittest.TestCase):
    def test_defaults_valid_and_presets(self):
        k, prov = knobs.load()
        self.assertEqual(k["loop"]["pass_score"], 8.5)
        self.assertEqual(prov["loop.pass_score"], "default")
        k2, prov2 = knobs.load("us-reach")
        self.assertEqual(k2["profile"]["currency"], "USD")
        self.assertEqual(prov2["profile.currency"], "preset:us-reach")

    def test_validation_rejects_bad_values(self):
        k, _ = knobs.load()
        k["loop"]["pass_score"] = 11
        k["search"]["date_posted"] = "year"
        errs = knobs.validate(k)
        self.assertTrue(any("pass_score" in e for e in errs))
        self.assertTrue(any("date_posted" in e for e in errs))

    def test_set_writes_user_file(self):
        with redirect_stdout(io.StringIO()):
            knobs.cmd_set("ranking.select_top_n", "7")
        k, prov = knobs.load()
        self.assertEqual(k["ranking"]["select_top_n"], 7)
        self.assertEqual(prov["ranking.select_top_n"], "user")
        Path(os.environ["GIMME_JOB_KNOBS"]).unlink()


class TestDedupeFilters(unittest.TestCase):
    def setUp(self):
        self.k, _ = knobs.load()

    def test_dedupe_merges_same_role_across_sources(self):
        a = job(1, source="greenhouse", description="short")
        b = job(2, source="linkedin", url="https://linkedin.com/jobs/view/2", title="Sr. Applied AI Engineer")
        out = dedupe.dedupe([a, b])
        self.assertEqual(len(out), 1)
        self.assertEqual(sorted(out[0]["sources"]), ["greenhouse", "linkedin"])
        self.assertEqual(out[0]["description"], JD)  # richer text kept

    def test_drop_reasons(self):
        self.assertEqual(dedupe.drop_reason(job(1, title="Director of AI"), self.k), "excluded title")
        self.assertEqual(dedupe.drop_reason(job(1, company="Robert Half Staffing"), self.k), "agency")
        self.assertEqual(dedupe.drop_reason(job(1, description="Sell cars."), self.k), "missing must_have_any")
        self.assertEqual(dedupe.drop_reason(job(1, posted_at="2001-01-01"), self.k), "too old")
        self.assertEqual(dedupe.drop_reason(job(1), self.k), "")


class TestRank(unittest.TestCase):
    def test_pre_score_orders_fit_first(self):
        k, _ = knobs.load()
        tax = rank.load_taxonomy()
        mine = {"Python", "RAG", "MCP", "AI Agents", "Tool Calling", "LLM Evaluation", "Kubernetes", "Terraform", "FastAPI", "LLM"}
        good, _ = rank.pre_score(job(1), k, tax, mine)
        bad, _ = rank.pre_score(job(2, title="Java Developer", description="Java Spring 10+ years", salary_max=60000), k, tax, mine)
        self.assertGreater(good, bad)
        self.assertGreater(good, 60)

    def test_years_asked(self):
        self.assertEqual(rank.years_asked("at least 2 years of experience"), 2)
        self.assertEqual(rank.years_asked("5+ years including 2+ years leading"), 2)
        self.assertIsNone(rank.years_asked("no years mentioned"))


TEX = r"""\documentclass{resume}
\begin{document}
\begin{rSection}{Experience}
\textbf{Developer} \hfill Jan 2026 - Aug 2026\\
Kinaxis \hfill Ottawa
\begin{itemize}
    \itemsep -3pt {}
    \item Tiered model routing cut token cost 48\% at equal task success.
\end{itemize}
\end{rSection}
\end{document}
"""
FACTS = {"skills": ["Python"], "locked": {"employers": ["Kinaxis"], "dates": ["Jan 2026 - Aug 2026"]},
         "facts": [{"id": "F1", "claim": "tiered model routing cut token cost 48%", "metrics": ["48%"]}]}


class TestFactGate(unittest.TestCase):
    def test_pass_on_true_facts(self):
        self.assertEqual(facts.check(TEX, FACTS)["verdict"], "PASS")

    def test_blocks_rounding_up_and_new_numbers_and_locked(self):
        r = facts.check(TEX.replace("48\\%", "50\\%"), FACTS)
        self.assertEqual(r["verdict"], "BLOCK")
        self.assertTrue(any("rounded up" in b for b in r["blocks"]))
        r2 = facts.check(TEX.replace("at equal", "for 300 users at equal"), FACTS)
        self.assertTrue(any("'300'" in b for b in r2["blocks"]))
        r3 = facts.check(TEX.replace("Kinaxis", "Google"), FACTS)
        self.assertTrue(any("locked employer" in b for b in r3["blocks"]))


class TestLint(unittest.TestCase):
    def test_flags_tool_soup_and_ampersand(self):
        k, _ = knobs.load()
        tex = TEX.replace("Tiered model routing cut token cost 48\\% at equal task success.",
                          "Used Kubernetes, Terraform, Docker, ArgoCD and Helm \\& more for deploys.")
        r = lint_tex.lint(tex, k["resume"]["lint"])
        self.assertTrue(any("tools" in w for w in r["warnings"]))
        self.assertTrue(any("no number" in w for w in r["warnings"]))
        self.assertTrue(any("banned" in e for e in r["errors"]))
        self.assertEqual(len(lint_tex.bullets(TEX)), 1)  # \itemsep is not a bullet


class TestPiiGuard(unittest.TestCase):
    def test_scan_blocks_phone_email_pdf(self):
        from scripts import pii_guard
        d = Path(tempfile.mkdtemp())
        (d / "a.md").write_text("call (647) 227-1538")
        (d / "b.md").write_text("mail someone@gmail.com")
        (d / "c.md").write_text("clean text")
        (d / "r.pdf").write_bytes(b"%PDF")
        hits = pii_guard.scan([str(d / x) for x in ("a.md", "b.md", "c.md", "r.pdf")])
        self.assertEqual(len(hits), 3)
        self.assertFalse(any("c.md" in h for h in hits))


class TestComposioIngest(unittest.TestCase):
    def test_linkedin_and_jsearch_shapes(self):
        d = Path(tempfile.mkdtemp())
        (d / "JOB_SEARCH_JOBS_API_LINKEDIN_SEARCH_JOBS-1.json").write_text(json.dumps({"data": {"result": {"data": [
            {"companyName": "Thomson Reuters", "datePosted": "2026-10-27", "id": "4450900129", "location": "Toronto, Ontario, Canada",
             "linkedinUrl": "https://ca.linkedin.com/jobs/view/x-4450900129", "title": "Senior AI Engineer, Agentic AI"}]}}}))
        (d / "JOB_SEARCH_JSEARCH_SEARCH_JOBS-1.json").write_text(json.dumps({"data": {"data": [
            {"job_id": "abc", "job_title": "AI Developer", "employer_name": "WSP", "job_apply_link": "https://wsp.com/j/1",
             "job_city": "Toronto", "job_country": "CA", "job_min_salary": 95500, "job_max_salary": 130800, "job_salary_period": "YEAR"}]}}))
        rows = composio_ingest.ingest(sorted(str(p) for p in d.iterdir()))
        by = {r["source"]: r for r in rows}
        self.assertEqual(by["linkedin"]["company"], "Thomson Reuters")
        self.assertEqual(by["jsearch"]["salary_max"], 130800)
        self.assertEqual(by["jsearch"]["salary_period"], "year")

    def test_plan_respects_knobs(self):
        k, _ = knobs.load()
        calls = composio_ingest.plan(k)
        slugs = {c["tool_slug"] for c in calls}
        self.assertIn("JOB_SEARCH_JOBS_API_LINKEDIN_SEARCH_JOBS", slugs)
        self.assertNotIn("JOB_SEARCH_JOBS_API_INDEED_SEARCH_JOBS", slugs)  # off by default
        li = next(c for c in calls if c["tool_slug"].endswith("LINKEDIN_SEARCH_JOBS"))
        self.assertIn("onSite", li["arguments"]["workplace_types"])
        self.assertLessEqual(len(calls), k["budget"]["max_composio_calls"])


class TestInbox(unittest.TestCase):
    def test_alert_html_to_jobs(self):
        html = ('<a href="https://www.linkedin.com/comm/jobs/view/4474609595/?trk=x">Applied AI Engineer</a>'
                '<a href="https://www.linkedin.com/comm/jobs/view/4474609595/">View job</a>'
                '<a href="https://ca.indeed.com/rc/clk?jk=1a2b3c&from=ja">AI Developer</a>')
        jobs = inbox_scan.jobs_from_html(html)
        urls = {j.url: j.title for j in jobs}
        self.assertEqual(urls["https://www.linkedin.com/jobs/view/4474609595"], "Applied AI Engineer")
        self.assertIn("https://www.indeed.com/viewjob?jk=1a2b3c", urls)


class TestLedgerCardsVersions(unittest.TestCase):
    def test_ledger_summary_and_cards(self):
        rd = common.new_run()
        for st, why in [("ok", ""), ("ok", ""), ("failed", "429 rate limit"), ("failed", "429 rate limit"), ("failed", "blocked host")]:
            common.append_jsonl(rd / "ledger.jsonl", {"tool": "composio", "source": "LINKEDIN_GET_JOB", "status": st, "reason": why, "cost": 0.0002})
        s = ledger.summary(rd.name)
        self.assertEqual(s["total"], {"calls": 5, "ok": 2, "failed": 3, "cost": 0.001})
        self.assertEqual(s["by_source"]["LINKEDIN_GET_JOB"]["reasons"]["429 rate limit"], 2)
        common.write_json(rd / "funnel.json", {"found": 10, "unique": 8, "after_filters": 6, "kept": 5, "liveness": {"dead": 1},
                                               "dropped": {"agency": 2}, "by_source": {"greenhouse": 6, "linkedin": 4}})
        common.write_json(rd / "selected.json", {"selected": [{**job(1), "pre_score": 80.1, "ah_score": 4.4,
                                                              "salary": [120000, 150000, "CAD"], "why": "agents + MCP"}]})
        text = cards.card_tools(rd) + cards.card_jobs(rd) + cards.card_selected(rd)
        self.assertIn("429 rate limit ×2", text)
        self.assertIn("**10** found", text)
        self.assertIn("Applied AI Engineer", text)

    def test_ledger_classifies_composio_hook_event(self):
        rd = common.new_run()
        ev = {"tool_name": "mcp__composio__COMPOSIO_MULTI_EXECUTE_TOOL",
              "tool_input": {"tools": [{"tool_slug": "A"}, {"tool_slug": "B"}]},
              "tool_response": {"data": {"results": [{"response": {"successful": True}},
                                                     {"error": "Instant Tools are experiencing high usage", "response": {"successful": False}}]}}}
        ledger.hook_record(ev)
        rows = list(common.read_jsonl(rd / "ledger.jsonl"))
        self.assertEqual([r["status"] for r in rows], ["ok", "failed"])
        self.assertEqual(rows[1]["reason"], "429 rate limit")

    def test_versions(self):
        k, _ = knobs.load()
        v1 = Path(TMP) / "versions" / "v1"
        v1.mkdir(parents=True, exist_ok=True)
        (v1 / "resume-v1.tex").write_text(TEX)
        common.write_json(v1 / "judge.json", {"score": 7.2})
        n = version.new_version(k, run="r1")
        self.assertEqual(n, 2)
        self.assertTrue((Path(TMP) / "versions" / "v2" / "resume-v2.tex").exists())
        self.assertIn("parent v1", (Path(TMP) / "versions" / "v2" / "changes.md").read_text())
        common.write_json(Path(TMP) / "versions" / "v2" / "judge.json", {"score": 8.7})
        self.assertEqual(version.best(k), (2, 8.7))


class TestRegistry(unittest.TestCase):
    def test_all_145_scanners_registered_with_tests(self):
        provs = _registry.all_providers()
        self.assertEqual(len(provs), 145)
        waves = {}
        for p in provs.values():
            waves[p.wave] = waves.get(p.wave, 0) + 1
        self.assertEqual(waves, {"W1": 20, "W2": 25, "W3": 23, "W4": 25, "W5": 35, "W6": 17})
        tests = {p.stem[5:] for p in (Path(__file__).parent / "providers").glob("test_*.py")}
        import importlib
        for name, p in provs.items():
            mod = type(p).__module__.rsplit(".", 1)[-1]
            self.assertIn(mod, tests, f"no test file for scanner {name} ({mod})")


if __name__ == "__main__":
    unittest.main()
