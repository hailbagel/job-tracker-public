import json
import tempfile
import unittest
from pathlib import Path

from jobtracker.acquisition import AcquisitionResult
from jobtracker.patrick import generate_multi
from jobtracker.processing import process_success


def source(source_id, company):
    return {
        "id": source_id, "company": company, "careers_url": f"https://{source_id}.test/jobs",
        "country": "US", "region": "International", "sector": "Space/Rocket",
        "acquisition_mode": "api", "enabled": True, "priority": "B", "tags": ["patrick"],
        "adapter": "greenhouse", "adapter_config": {"url": f"https://{source_id}.test/api"},
    }


def result(source_id, company, location):
    return AcquisitionResult([{
        "id": f"{source_id}:7", "source_id": source_id, "source_job_id": "7",
        "title": "Construction Project Manager", "location": location, "company": company,
        "department": "Facilities", "link": f"https://{source_id}.test/7",
        "mission": "construction project management", "requirements": "",
        "benefits": "",
    }])


class MultiCompanyPatrickTests(unittest.TestCase):
    def test_aggregation_qualified_identity_coverage_and_privacy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            alpha, beta = source("alpha", "Alpha Space"), source("beta", "Beta Rocket")
            process_success(root, alpha, result("alpha", "Alpha Space", "Louisiana"), "2026-01-01T00:00:00Z")
            process_success(root, beta, result("beta", "Beta Rocket", "Berlin"), "2026-01-01T00:00:00Z")
            document = generate_multi(
                "configs/profiles/example.json", [alpha, beta], root, root / "patrick",
                "2026-01-02T00:00:00Z",
            )
            self.assertEqual({"Alpha Space", "Beta Rocket"}, {row["company"] for row in document["rankings"]})
            self.assertEqual({"alpha:7", "beta:7"}, {row["job_id"] for row in document["rankings"]})
            self.assertTrue(document["metadata"]["coverage_complete"])
            self.assertEqual(2, document["metadata"]["counts"]["scanned"])
            payload = (root / "patrick/patrick_targets.json").read_text(encoding="utf-8")
            self.assertNotIn("candidate_evidence", payload)
            self.assertNotIn("Fictional example evidence", payload)
            markdown = (root / "patrick/patrick_targets.md").read_text(encoding="utf-8")
            self.assertIn("Alpha Space", markdown)
            self.assertIn("Beta Rocket", markdown)

    def test_incomplete_source_is_reported_and_not_ranked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            alpha, missing = source("alpha", "Alpha Space"), source("missing", "Missing Space")
            process_success(root, alpha, result("alpha", "Alpha Space", "Texas"), "2026-01-01T00:00:00Z")
            document = generate_multi("configs/profiles/example.json", [alpha, missing], root, root / "patrick")
            self.assertFalse(document["metadata"]["coverage_complete"])
            self.assertEqual(["alpha:7"], [row["job_id"] for row in document["rankings"]])
            coverage = {item["source_id"]: item for item in document["metadata"]["source_coverage"]}
            self.assertEqual("unavailable", coverage["missing"]["status"])
            self.assertFalse(coverage["missing"]["coverage_complete"])


if __name__ == "__main__":
    unittest.main()
