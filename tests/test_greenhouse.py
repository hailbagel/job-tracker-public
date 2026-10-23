import json
import unittest

from analysis.profile_ranking import rank_job, split_qualifications
from jobtracker.acquisition import greenhouse
from tests.test_profile_ranking import profile


def source():
    return {
        "id": "rocket-factory-augsburg",
        "company": "Rocket Factory Augsburg",
        "adapter_config": {"url": "https://boards-api.greenhouse.io/v1/boards/rfa/jobs?content=true"},
    }


def acquire(job_id, title, content):
    payload = {"jobs": [{
        "id": job_id,
        "title": title,
        "absolute_url": f"https://job-boards.eu.greenhouse.io/rfa/jobs/{job_id}",
        "location": {"name": "Augsburg, Bavaria, Germany"},
        "departments": [{"name": "Program Management"}],
        "content": content,
    }]}
    return greenhouse(source(), fetch=lambda _url: json.dumps(payload).encode()).jobs[0]


RFA_4944174101 = """
&lt;h2&gt;About the Team&lt;/h2&gt;
&lt;p&gt;Support project management, planning &amp;amp; schedules.&lt;/p&gt;
&lt;h2&gt;Your Tasks&lt;/h2&gt;
&lt;ul&gt;&lt;li&gt;Manage institutional projects.&lt;/li&gt;&lt;/ul&gt;
&lt;h2&gt;Your Qualifications&lt;/h2&gt;
&lt;ul&gt;
  &lt;li&gt;Bachelor&#39;s degree or Master&#39;s degree in Aerospace Engineering or similar.&lt;/li&gt;
  &lt;li&gt;Work experience in project management.&lt;/li&gt;
&lt;/ul&gt;
&lt;h2&gt;We Offer&lt;/h2&gt;&lt;p&gt;Flexible working hours &amp;amp; home office.&lt;/p&gt;
"""


RFA_4997134101 = """
<h2>About the Team</h2><p>Quality assurance for aerospace production.</p>
<h2>Your Qualifications</h2>
<p><strong>Must-Have Skills</strong></p>
<ul>
  <li>Completed technical vocational training, apprenticeship, or equivalent technical qualification.</li>
  <li>At least 2 years of experience in Quality Assurance or Quality Control.</li>
</ul>
<p><strong>Nice-to-Have Skills</strong></p>
<ul><li>Experience in the aerospace industry.</li></ul>
<h2>We Offer</h2><p>Flexible working hours.</p>
"""


class GreenhouseRequirementsTests(unittest.TestCase):
    def test_4944174101_degree_is_normalized_and_blocks_unverified_green(self):
        item = acquire(
            "4944174101", "Institutional Project Manager (m/f/d)", RFA_4944174101
        )
        self.assertIn("Manage institutional projects", item["mission"])
        self.assertIn("Bachelor's degree", item["requirements"])
        self.assertIn("Flexible working hours & home office", item["benefits"])

        candidate = profile("unknown", threshold=1)
        result = rank_job(item, item, candidate)
        self.assertEqual("UNKNOWN", result["status"])
        self.assertIn("degree", {gate["gate"] for gate in result["hard_gates"]})

    def test_4997134101_required_and_optional_qualifications_stay_distinct(self):
        item = acquire(
            "4997134101", "Quality Assurance Inspector (m/f/d)", RFA_4997134101
        )
        basic, preferred, additional = split_qualifications(item["requirements"])
        self.assertIn("technical vocational training", basic)
        self.assertIn("2 years", basic)
        self.assertIn("aerospace industry", preferred)
        self.assertIsNone(additional)

        candidate = profile(threshold=1)
        candidate["role_families"].append("QA/QC")
        result = rank_job(item, item, candidate)
        self.assertEqual("UNKNOWN", result["status"])
        self.assertTrue({
            "required_years", "required_credential:technical qualification",
        }.issubset({gate["gate"] for gate in result["hard_gates"]}))
        self.assertNotIn("aerospace industry", " ".join(
            gate["requirement_evidence"]["excerpt"] for gate in result["hard_gates"]
        ))

    def test_missing_or_malformed_requirements_cannot_become_green_from_keywords(self):
        for content in (
            "<h2>Your Tasks</h2><p>Construction project management, schedule and cost.</p>",
            "<h2>Your Qualifictions</h2><p>Construction project management experience.</p>",
            "",
        ):
            with self.subTest(content=content):
                item = acquire("synthetic", "Construction Project Manager", content)
                result = rank_job(item, item, profile(threshold=1))
                self.assertEqual("UNKNOWN", result["status"])
                self.assertIn(
                    "requirements_evaluation",
                    {gate["gate"] for gate in result["hard_gates"]},
                )

    def test_preferred_only_greenhouse_content_stays_soft(self):
        item = acquire(
            "preferred-only",
            "Construction Project Manager",
            """
            <h2>Role Mission</h2><p>Lead construction project management.</p>
            <h2>Preferred Qualifications</h2><p>Bachelor's degree.</p>
            """,
        )
        basic, preferred, additional = split_qualifications(item["requirements"])
        self.assertIsNone(basic)
        self.assertIn("Bachelor's degree", preferred)
        self.assertIsNone(additional)

        result = rank_job(item, item, profile(threshold=1))
        self.assertEqual("UNKNOWN", result["status"])
        self.assertEqual(
            {"requirements_evaluation"},
            {gate["gate"] for gate in result["hard_gates"]},
        )
        self.assertIn("Bachelor's degree", result["soft_gaps"][0]["requirement"])

    def test_fully_evidenced_required_criteria_can_still_be_green(self):
        item = acquire(
            "control",
            "Construction Project Manager",
            """
            <h2>Your Tasks</h2><p>Lead construction project management.</p>
            <h2>Requirements</h2>
            <ul><li>Bachelor's degree.</li><li>2 years project management experience.</li></ul>
            """,
        )
        candidate = profile(threshold=1)
        candidate["qualification_evidence"] = [{
            "kind": "experience", "name": "project management", "years": 2,
            "leadership": False, "status": "verified",
            "evidence": {"source": "fixture", "claim_id": "EXP-2"},
        }]
        result = rank_job(item, item, candidate)
        self.assertEqual("GREEN", result["status"])
        self.assertEqual([], result["hard_gates"])


if __name__ == "__main__":
    unittest.main()
