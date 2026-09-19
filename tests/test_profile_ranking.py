import csv
import hashlib
import json
import os
import subprocess
import sys
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from analysis.profile_ranking import classify_family, generate, rank_job, split_qualifications


REQUIRED_KEYS = {
    "job_id", "requisition_id", "title", "location", "url", "first_published", "updated_at",
    "role_family", "fit_score", "fit_reasons", "hard_gates", "soft_gaps", "degree_rule",
    "experience_in_lieu", "work_authorization_signal", "itar_signal", "recommended_profile_focus", "status",
}


def profile(status="verified", threshold=65):
    evidence = {"source": "fixture", "claim_id": "E-1"} if status == "verified" else None
    return {
        "schema_version": 1,
        "profile_id": "fixture",
        "display_name": "Fixture Candidate",
        "evidence_version": "fixture-v1",
        "role_families": ["Construction Project Management", "Project Controls"],
        "preferred_locations": ["Louisiana"],
        "strong_match_threshold": threshold,
        "capabilities": [
            {"name": "Construction", "keywords": ["construction", "project management"], "evidence": {"source": "fixture", "claim_id": "C-1"}},
            {"name": "Controls", "keywords": ["schedule", "cost"], "evidence": {"source": "fixture", "claim_id": "C-2"}},
        ],
        "eligibility": {
            "work_authorization": {"status": status, "evidence": evidence},
            "itar": {"status": status, "evidence": evidence},
            "degree": {"status": status, "evidence": evidence},
        },
    }


def job(job_id="100", title="Construction Project Manager", location="Pecan Island, Louisiana", requisition="REQ-1"):
    return {
        "id": job_id, "title": title, "location": location, "company": "SpaceX", "department": "Facilities",
        "link": f"https://example.test/jobs/{job_id}", "requisition_id": requisition,
        "first_published": "2026-01-01", "updated_at": "2026-01-02", "scrape_timestamp": "clock-a",
    }


def detail(item, suffix=""):
    return {
        "title": item["title"], "location": item["location"], "company": "SpaceX", "department": item["department"],
        "link": item["link"], "mission": "Lead construction project management, schedule and cost work.",
        "requirements": "BASIC QUALIFICATIONS:\nBachelor's degree or 8 years experience in lieu of degree.\nMust be authorized to work in the U.S. and eligible under ITAR as a U.S. person.\nPREFERRED QUALIFICATIONS:\nAutoCAD and welding certification.",
        "benefits": "Compensation $100,000 - $120,000/year", "scrape_timestamp": f"clock-{suffix}",
    }


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


class RankingSemanticsTests(unittest.TestCase):
    def test_basic_preferred_and_unknown_gate_cannot_be_green(self):
        item = job()
        basic, preferred, additional = split_qualifications(detail(item)["requirements"])
        self.assertIn("Bachelor", basic)
        self.assertIn("AutoCAD", preferred)
        self.assertIsNone(additional)
        result = rank_job(item, detail(item), profile("unknown", threshold=1))
        self.assertEqual("UNKNOWN", result["status"])
        self.assertEqual({"work_authorization", "itar", "degree_or_experience"}, {gate["gate"] for gate in result["hard_gates"]})
        self.assertTrue(all(gate["candidate_status"] == "unknown" for gate in result["hard_gates"]))
        self.assertIn("AutoCAD", result["soft_gaps"][0]["requirement"])

    def test_verified_evidence_can_be_green_and_preserves_required_fields(self):
        result = rank_job(job(), detail(job()), profile())
        self.assertEqual("GREEN", result["status"])
        self.assertTrue(REQUIRED_KEYS.issubset(result))
        self.assertEqual("100", str(result["job_id"]))
        self.assertEqual("REQ-1", result["requisition_id"])
        self.assertTrue(result["experience_in_lieu"])
        self.assertTrue(all(reason["candidate_evidence"] for reason in result["fit_reasons"]))

    def test_preferred_degree_is_soft_not_hard(self):
        item = job()
        details = detail(item)
        details["requirements"] = "BASIC QUALIFICATIONS:\n5 years construction project management.\nPREFERRED QUALIFICATIONS:\nBachelor's degree."
        result = rank_job(item, details, profile())
        self.assertNotIn("degree", {gate["gate"] for gate in result["hard_gates"]})
        self.assertIn("Bachelor", result["soft_gaps"][0]["requirement"])
    def test_required_years_domain_software_trade_and_leadership_are_hard_gates(self):
        item = job()
        details = detail(item)
        details["requirements"] = "BASIC QUALIFICATIONS:\n10+ years civil construction leadership. Expert AutoCAD required. Welding and piping required."
        result = rank_job(item, details, profile(threshold=1))
        gate_names = {gate["gate"] for gate in result["hard_gates"]}
        self.assertEqual("UNKNOWN", result["status"])
        self.assertTrue({
            "required_years", "required_domain", "required_leadership",
            "required_software:autocad", "required_trade:welding", "required_trade:piping",
        }.issubset(gate_names))
        self.assertTrue(all(gate["candidate_status"] == "unknown" for gate in result["hard_gates"]))

        known = profile(threshold=1)
        known["qualification_evidence"] = [
            {"kind": "experience", "name": "civil construction", "years": 5, "leadership": False, "status": "verified", "evidence": {"source": "fixture", "claim_id": "EXP-LOW"}},
            {"kind": "software", "name": "autocad", "status": "unsupported", "evidence": {"source": "fixture", "claim_id": "SW-NO"}},
            {"kind": "trade", "name": "welding", "status": "unsupported", "evidence": {"source": "fixture", "claim_id": "TR-NO-1"}},
            {"kind": "trade", "name": "piping", "status": "unsupported", "evidence": {"source": "fixture", "claim_id": "TR-NO-2"}},
        ]
        known_result = rank_job(item, details, known)
        self.assertEqual("RED", known_result["status"])
        self.assertIn("unsupported", {gate["candidate_status"] for gate in known_result["hard_gates"]})

    def test_explicit_verified_qualification_claims_can_satisfy_required_facts(self):
        item = job()
        details = detail(item)
        details["requirements"] = "BASIC QUALIFICATIONS:\n10+ years civil construction leadership. Expert AutoCAD required. Welding and piping required."
        qualified = profile(threshold=1)
        qualified["qualification_evidence"] = [
            {"kind": "experience", "name": "civil construction", "years": 12, "leadership": True, "status": "verified", "evidence": {"source": "fixture", "claim_id": "EXP-12"}},
            {"kind": "software", "name": "autocad", "status": "verified", "evidence": {"source": "fixture", "claim_id": "SW-1"}},
            {"kind": "trade", "name": "welding", "status": "verified", "evidence": {"source": "fixture", "claim_id": "TR-1"}},
            {"kind": "trade", "name": "piping", "status": "verified", "evidence": {"source": "fixture", "claim_id": "TR-2"}},
        ]
        result = rank_job(item, details, qualified)
        self.assertEqual("GREEN", result["status"])
        self.assertEqual([], result["hard_gates"])

    def test_degree_or_eight_years_experience_is_a_real_alternative(self):
        item = job()
        details = detail(item)
        details["requirements"] = "BASIC QUALIFICATIONS:\nBachelor degree or 8 years civil construction experience in lieu of degree."
        candidate = profile("unknown", threshold=1)
        candidate["eligibility"]["work_authorization"] = profile()["eligibility"]["work_authorization"]
        candidate["eligibility"]["itar"] = profile()["eligibility"]["itar"]
        candidate["qualification_evidence"] = [
            {"kind": "experience", "name": "civil construction", "years": 8, "leadership": False, "status": "verified", "evidence": {"source": "fixture", "claim_id": "EXP-8"}},
        ]
        result = rank_job(item, details, candidate)
        self.assertNotIn("degree_or_experience", {gate["gate"] for gate in result["hard_gates"]})
        self.assertEqual("GREEN", result["status"])

        candidate["qualification_evidence"][0]["years"] = 7
        insufficient = rank_job(item, details, candidate)
        self.assertIn("degree_or_experience", {gate["gate"] for gate in insufficient["hard_gates"]})
        self.assertNotEqual("GREEN", insufficient["status"])

        details["requirements"] = "BASIC QUALIFICATIONS:\nBachelor degree or 8 years civil construction experience in lieu of degree. 10+ years civil construction leadership required."
        candidate["qualification_evidence"][0]["years"] = 8
        boundary = rank_job(item, details, candidate)
        boundary_gates = {gate["gate"] for gate in boundary["hard_gates"]}
        self.assertNotIn("degree_or_experience", boundary_gates)
        self.assertTrue({"required_years", "required_leadership"}.issubset(boundary_gates))

        candidate["qualification_evidence"][0].update({"name": "mechanical construction", "years": 12, "leadership": True})
        wrong_domain = rank_job(item, details, candidate)
        self.assertIn("degree_or_experience", {gate["gate"] for gate in wrong_domain["hard_gates"]})

    def test_specific_family_precedence_and_all_required_families(self):
        cases = {
            "Mechanical Construction Manager": "Mechanical Construction",
            "Construction Project Manager": "Construction Project Management",
            "Construction Superintendent": "Construction Superintendent / Field Execution",
            "Structural Steel Engineer": "Structural / Steel",
            "Facilities Infrastructure Engineer": "Facilities / Infrastructure",
            "Project Controls Scheduler": "Project Controls",
            "Quality Control Inspector": "QA/QC",
            "Commissioning Turnover Manager": "Commissioning / Turnover",
            "Utilities Power Engineer": "Utilities / Power",
            "Tooling Installation Manager": "Tooling / Installation",
        }
        for title, expected in cases.items():
            with self.subTest(title=title):
                self.assertEqual(expected, classify_family(title, title))


class ExportContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.data = self.root / "data" / "spacex"
        self.output = self.root / "private-output"
        self.profile_path = self.root / "profile.json"
        self.schema_path = self.root / "schema.json"
        self.schema_path.write_bytes(Path("configs/profiles/schema.json").read_bytes())
        self.profile_path.write_text(json.dumps(profile()), encoding="utf-8")
        self.jobs = [job("100", requisition="DUP"), job("101", title="Project Controls Manager", location="Brownsville, Texas", requisition="DUP")]
        self.details = [detail(self.jobs[0], "one"), detail(self.jobs[1], "two")]
        self._write_snapshot("hash-1", "2026-01-01T00:00:00Z")

    def tearDown(self):
        self.temp.cleanup()

    def _write_snapshot(self, data_hash, observed, complete=True):
        write_csv(self.data / "processed" / "jobs_latest.csv", self.jobs)
        write_csv(self.data / "processed" / "job_details.csv", self.details)
        acquisition = {
            "observed_at": observed, "data_changed_at": "2026-01-01T00:00:00Z", "data_hash": data_hash,
            "source_records": len(self.jobs), "records_written": len(self.jobs), "coverage_complete": complete,
        }
        (self.data / "processed" / "acquisition.json").write_text(json.dumps(acquisition), encoding="utf-8")

    def _hashes(self):
        return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in self.output.iterdir()}

    def test_source_id_not_duplicate_requisition_is_identity_and_formats_align(self):
        result = generate(self.profile_path, self.data, self.output, "2026-01-02T00:00:00Z")
        document = result["document"]
        self.assertEqual({"100", "101"}, {str(row["job_id"]) for row in document["rankings"]})
        self.assertEqual({"DUP"}, {row["requisition_id"] for row in document["rankings"]})
        with (self.output / "spacex_targets.csv").open(newline="", encoding="utf-8") as handle:
            csv_rows = list(csv.DictReader(handle))
        self.assertEqual(len(document["rankings"]), len(csv_rows))
        self.assertEqual([str(row["job_id"]) for row in document["rankings"]], [row["job_id"] for row in csv_rows])
        markdown = (self.output / "spacex_targets.md").read_text(encoding="utf-8")
        self.assertIn("Scanned: 2", markdown)
        self.assertLessEqual(len(document["verified_strong_targets"]), 10)

    def test_unchanged_semantics_preserve_all_bytes_and_generation_time(self):
        first = generate(self.profile_path, self.data, self.output, "2026-01-02T00:00:00Z")
        before = self._hashes()
        before_mtimes = {path.name: path.stat().st_mtime_ns for path in self.output.iterdir()}
        self.details[0]["scrape_timestamp"] = "execution-clock-changed"
        self._write_snapshot("hash-1", "2026-01-03T00:00:00Z")
        second = generate(self.profile_path, self.data, self.output, "2026-01-03T00:00:00Z")
        self.assertTrue(first["changed"])
        self.assertFalse(second["changed"])
        self.assertEqual(before, self._hashes())
        self.assertEqual("2026-01-02T00:00:00Z", second["document"]["metadata"]["generated_at"])
        self.assertEqual(before_mtimes, {path.name: path.stat().st_mtime_ns for path in self.output.iterdir()})

    def test_profile_and_rubric_inputs_invalidate_cached_result(self):
        generate(self.profile_path, self.data, self.output, "2026-01-02T00:00:00Z")
        changed_profile = profile()
        changed_profile["evidence_version"] = "fixture-v2"
        self.profile_path.write_text(json.dumps(changed_profile), encoding="utf-8")
        result = generate(self.profile_path, self.data, self.output, "2026-01-04T00:00:00Z")
        self.assertTrue(result["changed"])
        self.assertEqual("fixture-v2", result["document"]["metadata"]["profile_evidence_version"])

    def test_actual_schema_semantics_invalidate_cache_and_unchanged_schema_does_not(self):
        with patch("analysis.profile_ranking.PROFILE_SCHEMA_PATH", self.schema_path):
            first = generate(self.profile_path, self.data, self.output, "2026-01-02T00:00:00Z")
            replay = generate(self.profile_path, self.data, self.output, "2026-01-03T00:00:00Z")
            self.assertFalse(replay["changed"])

            schema = json.loads(self.schema_path.read_text(encoding="utf-8"))
            schema["required"].append("new_semantic_field")
            self.schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
            changed = generate(self.profile_path, self.data, self.output, "2026-01-04T00:00:00Z")

        self.assertTrue(changed["changed"])
        self.assertNotEqual(
            first["document"]["metadata"]["profile_schema_hash"],
            changed["document"]["metadata"]["profile_schema_hash"],
        )
        self.assertNotEqual(
            first["document"]["metadata"]["input_hash"],
            changed["document"]["metadata"]["input_hash"],
        )

    def test_missing_or_malformed_schema_preserves_previous_good_feed(self):
        with patch("analysis.profile_ranking.PROFILE_SCHEMA_PATH", self.schema_path):
            generate(self.profile_path, self.data, self.output, "2026-01-02T00:00:00Z")
            before = self._hashes()
            self.schema_path.unlink()
            with self.assertRaisesRegex(RuntimeError, "Profile schema is missing"):
                generate(self.profile_path, self.data, self.output, "2026-01-03T00:00:00Z")
            self.assertEqual(before, self._hashes())

            self.schema_path.write_text("{malformed", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Profile schema is malformed JSON"):
                generate(self.profile_path, self.data, self.output, "2026-01-04T00:00:00Z")
            self.assertEqual(before, self._hashes())

    def test_new_changed_removed_and_removed_not_current_strong(self):
        generate(self.profile_path, self.data, self.output, "2026-01-02T00:00:00Z")
        changed = self.jobs[0].copy()
        changed["location"] = "Bastrop, Texas"
        new = job("102", title="Construction Project Manager II", requisition="REQ-2")
        self.jobs = [changed, new]
        self.details = [detail(changed, "changed"), detail(new, "new")]
        self._write_snapshot("hash-2", "2026-01-05T00:00:00Z")
        document = generate(self.profile_path, self.data, self.output, "2026-01-05T00:00:00Z")["document"]
        self.assertEqual(["102"], [str(row["job_id"]) for row in document["new_relevant"]])
        self.assertEqual(["100"], [str(row["job_id"]) for row in document["materially_changed_relevant"]])
        self.assertEqual(["101"], [str(row["job_id"]) for row in document["removed_relevant"]])
        self.assertNotIn("101", {str(row["job_id"]) for row in document["verified_strong_targets"]})
        changed_hashes = self._hashes()
        replay = generate(self.profile_path, self.data, self.output, "2026-01-06T00:00:00Z")
        self.assertFalse(replay["changed"])
        self.assertEqual(changed_hashes, self._hashes())

    def test_incomplete_acquisition_preserves_previous_good_outputs(self):
        generate(self.profile_path, self.data, self.output, "2026-01-02T00:00:00Z")
        before = self._hashes()
        self._write_snapshot("partial", "2026-01-06T00:00:00Z", complete=False)
        with self.assertRaisesRegex(RuntimeError, "incomplete"):
            generate(self.profile_path, self.data, self.output, "2026-01-06T00:00:00Z")
        self.assertEqual(before, self._hashes())

    def test_markdown_has_required_detail_for_every_displayed_role(self):
        document = generate(self.profile_path, self.data, self.output, "2026-01-02T00:00:00Z")["document"]
        markdown = (self.output / "spacex_targets.md").read_text(encoding="utf-8")
        for label in ("Role family:", "Profile focus:", "Hard gates:", "Soft gaps:", "Fit reasons:"):
            self.assertEqual(sum(len(document[key]) for key in (
                "top_25", "verified_strong_targets", "louisiana_subset",
                "new_relevant", "materially_changed_relevant", "removed_relevant",
            )), markdown.count(label))

    def test_missing_or_corrupt_companions_and_canonical_json_recover(self):
        first = generate(self.profile_path, self.data, self.output, "2026-01-02T00:00:00Z")
        original_json = (self.output / "spacex_targets.json").read_bytes()
        original_timestamp = first["document"]["metadata"]["generated_at"]
        (self.output / "spacex_targets.csv").unlink()
        (self.output / "spacex_targets.md").write_text("corrupt", encoding="utf-8")
        recovered = generate(self.profile_path, self.data, self.output, "2026-01-03T00:00:00Z")
        self.assertTrue(recovered["recovered"])
        self.assertEqual(original_json, (self.output / "spacex_targets.json").read_bytes())
        self.assertEqual(original_timestamp, recovered["document"]["metadata"]["generated_at"])
        self.assertTrue((self.output / "spacex_targets.csv").is_file())
        self.assertIn("Role family:", (self.output / "spacex_targets.md").read_text(encoding="utf-8"))

        (self.output / "spacex_targets.json").write_text("{broken", encoding="utf-8")
        canonical_recovery = generate(self.profile_path, self.data, self.output, "2026-01-04T00:00:00Z")
        self.assertTrue(canonical_recovery["recovered"])
        self.assertEqual(original_json, (self.output / "spacex_targets.json").read_bytes())

    def test_processed_csv_semantic_mutation_invalidates_cache(self):
        first = generate(self.profile_path, self.data, self.output, "2026-01-02T00:00:00Z")
        self.details[0]["requirements"] = self.details[0]["requirements"].replace(
            "Bachelor's degree", "Bachelor's degree and expert AutoCAD"
        )
        self._write_snapshot("hash-1", "2026-01-03T00:00:00Z")
        second = generate(self.profile_path, self.data, self.output, "2026-01-03T00:00:00Z")
        self.assertTrue(second["changed"])
        self.assertNotEqual(
            first["document"]["metadata"]["processed_input_hash"],
            second["document"]["metadata"]["processed_input_hash"],
        )
        self.assertIn("required_software:autocad", {
            gate["gate"] for gate in second["document"]["rankings"][0]["hard_gates"]
        })

    def test_publication_failure_keeps_complete_legacy_generation(self):
        generate(self.profile_path, self.data, self.output, "2026-01-02T00:00:00Z")
        current = self.output.resolve()
        self.output.unlink()
        shutil.copytree(current, self.output)
        before = self._hashes()
        changed_profile = profile()
        changed_profile["evidence_version"] = "fixture-v2"
        self.profile_path.write_text(json.dumps(changed_profile), encoding="utf-8")
        real_replace = os.replace
        call_count = [0]

        def fail_second_replace(source, destination):
            call_count[0] += 1
            if call_count[0] == 2:
                raise OSError("injected publication failure")
            return real_replace(source, destination)

        with patch("analysis.profile_ranking.os.replace", side_effect=fail_second_replace):
            with self.assertRaisesRegex(OSError, "injected publication failure"):
                generate(self.profile_path, self.data, self.output, "2026-01-03T00:00:00Z")
        self.assertEqual(3, call_count[0])
        self.assertTrue(self.output.is_dir())
        self.assertEqual(before, self._hashes())
        with (self.output / "spacex_targets.json").open(encoding="utf-8") as handle:
            self.assertEqual("fixture-v1", json.load(handle)["metadata"]["profile_evidence_version"])

    def test_pinned_generation_stays_consistent_while_fresh_reader_sees_update(self):
        generate(self.profile_path, self.data, self.output, "2026-01-02T00:00:00Z")
        generation_a = self.output.resolve(strict=True)
        names = ("spacex_targets.json", "spacex_targets.csv", "spacex_targets.md")
        expected_a = {name: (generation_a / name).read_bytes() for name in names}

        changed_profile = profile()
        changed_profile["evidence_version"] = "fixture-v2"
        self.profile_path.write_text(json.dumps(changed_profile), encoding="utf-8")
        generate(self.profile_path, self.data, self.output, "2026-01-03T00:00:00Z")

        self.assertEqual(expected_a, {name: (generation_a / name).read_bytes() for name in names})
        generation_b = self.output.resolve(strict=True)
        self.assertNotEqual(generation_a, generation_b)
        with (generation_b / "spacex_targets.json").open(encoding="utf-8") as handle:
            self.assertEqual("fixture-v2", json.load(handle)["metadata"]["profile_evidence_version"])

    def test_symlink_creation_failure_is_explicit_and_preserves_existing_feed(self):
        with patch("analysis.profile_ranking.os.symlink", side_effect=OSError("operation not permitted")):
            with self.assertRaisesRegex(RuntimeError, "requires directory symlink support"):
                generate(self.profile_path, self.data, self.output, "2026-01-02T00:00:00Z")
        self.assertFalse(self.output.exists())

        generate(self.profile_path, self.data, self.output, "2026-01-02T00:00:00Z")
        before = self._hashes()
        changed_profile = profile()
        changed_profile["evidence_version"] = "fixture-v2"
        self.profile_path.write_text(json.dumps(changed_profile), encoding="utf-8")
        with patch("analysis.profile_ranking.os.symlink", side_effect=OSError("operation not permitted")):
            with self.assertRaisesRegex(RuntimeError, "requires directory symlink support"):
                generate(self.profile_path, self.data, self.output, "2026-01-03T00:00:00Z")
        self.assertEqual(before, self._hashes())
        with (self.output / "spacex_targets.json").open(encoding="utf-8") as handle:
            self.assertEqual("fixture-v1", json.load(handle)["metadata"]["profile_evidence_version"])

    def test_deterministic_tie_breaker(self):
        self.jobs = [job("200", title="Construction Project Manager B"), job("199", title="Construction Project Manager A")]
        self.details = [detail(item) for item in self.jobs]
        self._write_snapshot("tie", "2026-01-07T00:00:00Z")
        rows = generate(self.profile_path, self.data, self.output, "2026-01-07T00:00:00Z")["document"]["rankings"]
        self.assertEqual(["Construction Project Manager A", "Construction Project Manager B"], [row["title"] for row in rows])


class PipelineIntegrationTests(unittest.TestCase):
    def test_normal_pipeline_exposes_provider_filter_and_profile_stage(self):
        result = subprocess.run([sys.executable, "run_pipeline.py", "--help"], text=True, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("--company", result.stdout)
        source = Path("run_pipeline.py").read_text(encoding="utf-8")
        self.assertIn('"script": "analysis/profile_ranking.py"', source)
        self.assertIn('company.lower() == "spacex"', source)


if __name__ == "__main__":
    unittest.main()
