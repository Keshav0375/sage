import unittest

from scripts.extract import (benefits, company, contacts, dates, education, employment, location, salary, skills,
                             title, work_auth, years)
from . import fixtures as F


class TitleTests(unittest.TestCase):
    def test_levels_families(self):
        r = title.extract("", {"title": "Senior AI Engineer - Agentic AI (m/f/d)"})
        self.assertEqual((r["level"], r["family"]), ("senior", "ai_engineer"))
        self.assertEqual(title.extract("", {"title": "Junior AI Developer"})["level"], "junior")
        self.assertEqual(title.extract("", {"title": "Staff Machine Learning Engineer"})["family"], "ml_engineer")
        self.assertEqual(title.extract("", {"title": "Forward Deployed Engineer"})["family"], "fde")
        self.assertEqual(title.extract("", {"title": "Engineering Manager, Platform"})["level"], "manager")

    def test_from_text_and_empty(self):
        self.assertEqual(title.extract(F.CGI)["title"], "Agentic AI Developer")
        self.assertEqual(title.extract("")["title"] if title.extract("") else "", "")


class LocationTests(unittest.TestCase):
    def test_tr(self):
        r = location.extract(F.TR)
        self.assertEqual((r["city"], r["region"], r["country"], r["workplace"]), ("Toronto", "ON", "CA", "hybrid"))

    def test_cgi_ottawa(self):
        r = location.extract(F.CGI)
        self.assertEqual((r["city"], r["region"], r["country"]), ("Ottawa", "ON", "CA"))
        self.assertNotIn("workplace", r)

    def test_remote_region(self):
        r = location.extract("This is a fully remote role. Remote within Canada only.")
        self.assertEqual(r["workplace"], "remote")
        self.assertEqual(r["remote_regions"], ["CA"])

    def test_job_field(self):
        self.assertEqual(location.extract("x", {"location": "Berlin, Germany", "workplace": "on-site"})["workplace"], "onsite")


class SalaryTests(unittest.TestCase):
    def test_tr(self):
        r = salary.extract(F.TR)
        self.assertEqual((r["salary_min"], r["salary_max"], r["currency"], r["salary_period"]), (100000, 145000, "CAD", "year"))

    def test_wsp_ignores_years(self):
        r = salary.extract(F.WSP, {"country": "CA"})
        self.assertEqual((r["salary_min"], r["salary_max"], r["currency"]), (95500, 130800, "CAD"))

    def test_k_and_code_prefix(self):
        r = salary.extract("Salary: $100K–$145K")
        self.assertEqual((r["salary_min"], r["salary_max"]), (100000, 145000))
        r = salary.extract("Pay range CAD 95,500 – 130,800")
        self.assertEqual((r["salary_min"], r["salary_max"], r["currency"]), (95500, 130800, "CAD"))

    def test_hourly(self):
        self.assertEqual(salary.extract("Pay: $35 - $45 per hour")["salary_period"], "hour")

    def test_none(self):
        self.assertEqual(salary.extract("5 to 15 years of experience, 2-3 teams"), {})


class YearsTests(unittest.TestCase):
    def test_cases(self):
        self.assertEqual(years.extract(F.TR)["years_min"], 2)
        self.assertEqual(years.extract(F.CGI)["years_min"], 3)
        self.assertEqual(years.extract(F.CGI)["or_equivalent"], True)
        r = years.extract(F.FIRSTNATIONAL)
        self.assertEqual((r["years_min"], r["years_max"]), (5, 15))
        self.assertEqual(years.extract(F.WSP)["years_min"], 5)
        self.assertEqual(years.extract("minimum of three (3) years of experience")["years_min"], 3)
        self.assertEqual(years.extract("We have grown for 10 years. Great culture."), {})


class SkillsTests(unittest.TestCase):
    def test_split(self):
        r = skills.extract(F.TR)
        for s in ("Python", "SQL", "RAG", "Docker"):
            self.assertIn(s, r["required"])
        self.assertIn("Kubernetes", r["nice_to_have"])
        self.assertNotIn("Kubernetes", r["required"])

    def test_asset_heading(self):
        r = skills.extract(F.CGI)
        self.assertIn("Kubernetes", r["nice_to_have"])
        self.assertIn("Java", r["required"])

    def test_word_boundary(self):
        r = skills.extract("Requirements\n- JavaScript\n- We like to go to market and Go to the moon")
        self.assertIn("JavaScript", r["required"])
        self.assertNotIn("Java", r["required"])
        self.assertNotIn("Go", r["required"])
        self.assertIn("Go", skills.extract("Requirements\n- Experience with Go and Rust")["required"])
        self.assertIn("C#", skills.extract("Requirements\n- C# and .NET")["required"])

    def test_empty(self):
        self.assertEqual(skills.extract("Be nice."), {})


class EducationTests(unittest.TestCase):
    def test_cases(self):
        self.assertEqual(education.extract(F.TR), {"degree": "bachelor", "or_equivalent": True})
        self.assertEqual(education.extract(F.WSP)["degree"], "master")
        self.assertEqual(education.extract(F.ERICSSON), {})   # master only "preferred"
        self.assertEqual(education.extract("No degree required.")["degree"], "none")


class WorkAuthTests(unittest.TestCase):
    def test_cases(self):
        self.assertEqual(work_auth.extract(F.ERICSSON)["sponsorship"], "not_offered")
        self.assertEqual(work_auth.extract(F.TR)["sponsorship"], "not_offered")
        self.assertEqual(work_auth.extract(F.CGI)["clearance"], "Reliability Status")
        self.assertEqual(work_auth.extract("Visa sponsorship is available for this role.")["sponsorship"], "offered")
        self.assertTrue(work_auth.extract("Must be a Canadian citizen.")["citizenship_required"])
        self.assertEqual(work_auth.extract("Great team."), {})


class EmploymentTests(unittest.TestCase):
    def test_cases(self):
        self.assertEqual(employment.extract(F.CGI)["employment"], "fulltime")
        r = employment.extract(F.FIRSTNATIONAL)
        self.assertEqual((r["employment"], r["contract_months"]), ("contract", 12))
        self.assertEqual(employment.extract("x", {"title": "AI Engineer Intern"})["employment"], "intern")
        self.assertEqual(employment.extract("x", {"employment": "part_time"})["employment"], "parttime")


class DatesTests(unittest.TestCase):
    def test_closing(self):
        r = dates.extract(F.FIRSTNATIONAL)
        self.assertEqual((r["closes_at"], r["posted_at"]), ("2026-11-23", "2026-11-02"))

    def test_variants(self):
        from datetime import date
        t = date(2026, 11, 14)
        self.assertEqual(dates.extract("Apply by 30 November 2026", None, t)["closes_at"], "2026-11-30")
        self.assertEqual(dates.extract("Job closes Nov 23", None, t)["closes_at"], "2026-11-23")
        self.assertEqual(dates.extract("Posted 3 days ago", None, t)["posted_at"], "2026-11-11")
        self.assertEqual(dates.extract("nothing"), {})


class ContactsTests(unittest.TestCase):
    def test_explicit_only(self):
        r = contacts.extract(F.ERICSSON)["contacts"]
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["email"], "jane.doe@ericsson.example")
        self.assertEqual(r[0]["name"], "Jane Doe")
        self.assertIn("Talent Acquisition", r[0]["title"])

    def test_none(self):
        self.assertEqual(contacts.extract("Apply on our website."), {})


class BenefitsCompanyTests(unittest.TestCase):
    def test_benefits(self):
        r = benefits.extract(F.TR)
        self.assertTrue(r["bonus"])
        for b in ("health", "dental", "retirement", "flexible_hours"):
            self.assertIn(b, r["benefits"])
        self.assertNotIn("equity", r)
        self.assertTrue(benefits.extract("Stock options and RSUs")["equity"])

    def test_company(self):
        self.assertEqual(company.extract(F.TR)["company_size"], "26000+")
        self.assertEqual(company.extract("We operate in the financial services industry.")["industry"], "financial services")
        self.assertEqual(company.extract("Hello"), {})
