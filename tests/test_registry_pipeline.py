import csv
import json
import tempfile
import unittest
from pathlib import Path

from jobtracker.acquisition import AcquisitionResult, acquire
from jobtracker.pipeline import normalize_existing_provider, run_source
from jobtracker.processing import COMMON_OUTPUTS, DETAIL_FIELDS, LATEST_FIELDS, process_success
from jobtracker.registry import RegistryError, get_source, load_registry


def source(**overrides):
    item = {
        "id": "demo", "company": "Demo", "careers_url": "https://example.test/jobs",
        "country": "US", "region": "International", "sector": "Space/Rocket",
        "acquisition_mode": "api", "enabled": True, "priority": "B", "tags": ["patrick"],
        "adapter": "greenhouse", "adapter_config": {"url": "https://example.test/api"},
    }
    item.update(overrides)
    return item


def write_registry(path, items):
    path.write_text(json.dumps({"schema_version": 1, "sources": items}), encoding="utf-8")


class RegistryTests(unittest.TestCase):
    def test_required_duplicate_and_manual_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "sources.json"
            write_registry(path, [source(), source()])
            with self.assertRaisesRegex(RegistryError, "Duplicate"):
                load_registry(path)
            broken = source()
            broken.pop("company")
            write_registry(path, [broken])
            with self.assertRaisesRegex(RegistryError, "company"):
                load_registry(path)
            write_registry(path, [source(acquisition_mode="manual_discovery", adapter=None)])
            with self.assertRaisesRegex(RegistryError, "manual_reason"):
                load_registry(path)

    def test_disabled_manual_and_dispatch(self):
        disabled = acquire(source(enabled=False))
        self.assertEqual("disabled", disabled.status)
        manual = acquire(source(acquisition_mode="manual_discovery", adapter=None, manual_reason="review required"))
        self.assertEqual("manual_discovery", manual.status)
        payload = json.dumps({"jobs": [{"id": 7, "title": "Site Manager", "absolute_url": "https://x/7", "location": {"name": "Texas"}}]}).encode()
        result = acquire(source(), fetch=lambda _url: payload)
        self.assertEqual("success", result.status)
        self.assertEqual("demo:7", result.jobs[0]["id"])

    def test_registered_rfa_greenhouse_adapter_remains_canonical(self):
        source_config = get_source("rocket-factory-augsburg")
        payload = json.dumps({"jobs": [{
            "id": 73,
            "title": "Propulsion Engineer",
            "location": {"name": "Augsburg, Germany"},
            "departments": [{"name": "Engineering"}],
            "absolute_url": "https://boards.greenhouse.io/rfa/jobs/73",
            "requisition_id": "RFA-73",
            "content": "<p>Develop rocket engines</p>",
        }]}).encode()

        with tempfile.TemporaryDirectory() as directory:
            run_source(source_config, directory, fetch=lambda _url: payload)
            processed = Path(directory) / "rocket-factory-augsburg/processed"
            with (processed / "jobs_latest.csv").open(newline="", encoding="utf-8") as handle:
                latest = list(csv.DictReader(handle))
            with (processed / "job_details.csv").open(newline="", encoding="utf-8") as handle:
                details = list(csv.DictReader(handle))

        self.assertEqual(LATEST_FIELDS, tuple(latest[0].keys()))
        self.assertEqual(DETAIL_FIELDS, tuple(details[0].keys()))
        self.assertEqual("rocket-factory-augsburg:73", latest[0]["id"])
        self.assertEqual("Augsburg, Germany", latest[0]["location"])
        self.assertEqual("Engineering", latest[0]["department"])
        self.assertIn("Develop rocket engines", details[0]["mission"])
        self.assertNotIn("requisition_id", latest[0])

    def test_success_outputs_and_source_qualified_collision(self):
        with tempfile.TemporaryDirectory() as directory:
            result_a = AcquisitionResult([{
                "id": "alpha:7", "source_id": "alpha", "source_job_id": "7",
                "title": "Project Manager", "location": "Texas", "company": "Alpha",
                "department": "Facilities", "link": "https://alpha/7",
                "mission": "", "requirements": "", "benefits": "",
            }])
            result_b = AcquisitionResult([dict(result_a.jobs[0], id="beta:7", source_id="beta", company="Beta", link="https://beta/7")])
            process_success(directory, source(id="alpha", company="Alpha"), result_a, "2026-01-01T00:00:00Z")
            process_success(directory, source(id="beta", company="Beta"), result_b, "2026-01-01T00:00:00Z")
            for source_id in ("alpha", "beta"):
                processed = Path(directory) / source_id / "processed"
                self.assertTrue(all((processed / name).is_file() for name in COMMON_OUTPUTS))
            with (Path(directory) / "alpha/processed/jobs_latest.csv").open(newline="", encoding="utf-8") as handle:
                self.assertEqual("alpha:7", next(csv.DictReader(handle))["id"])
            with (Path(directory) / "beta/processed/jobs_latest.csv").open(newline="", encoding="utf-8") as handle:
                self.assertEqual("beta:7", next(csv.DictReader(handle))["id"])

    def test_success_outputs_canonical_fields_and_blank_optional_values(self):
        with tempfile.TemporaryDirectory() as directory:
            job = {
                "id": "demo:8", "source_id": "demo", "source_job_id": "8",
                "title": "Systems Engineer", "link": "https://example.test/8",
                "company": "Demo", "provider_field": "must not leak",
                "location_id": "private-provider-value",
            }
            process_success(directory, source(), AcquisitionResult([job]), "2026-01-01T00:00:00Z")

            processed = Path(directory) / "demo/processed"
            expected_headers = {
                "jobs_latest.csv": LATEST_FIELDS,
                "job_details.csv": DETAIL_FIELDS,
                "job_history.csv": DETAIL_FIELDS + ("first_seen", "last_seen", "active"),
                "job_changes.csv": ("id", "source_id", "change", "title", "location", "observed_at"),
                "department_summary.csv": ("department", "count"),
                "location_summary.csv": ("location", "count"),
            }
            for filename, fields in expected_headers.items():
                with (processed / filename).open(newline="", encoding="utf-8") as handle:
                    self.assertEqual(fields, tuple(csv.DictReader(handle).fieldnames))

            for filename in ("jobs_latest.csv", "job_details.csv", "job_history.csv"):
                with (processed / filename).open(newline="", encoding="utf-8") as handle:
                    rows = list(csv.DictReader(handle))
                self.assertEqual("", rows[0]["location"])
                self.assertEqual("", rows[0]["department"])
                self.assertNotIn("provider_field", rows[0])
                self.assertNotIn("location_id", rows[0])

    def test_existing_provider_normalization_keeps_history_and_drops_legacy_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            source_config = source(
                id="legacy", company="Legacy Co", acquisition_mode="existing_provider",
                adapter="existing_provider",
            )
            processed = Path(directory) / "legacy/processed"
            processed.mkdir(parents=True)
            (processed / "jobs_latest.csv").write_text(
                "id,title,location_id,location,company,department,link,scrape_timestamp\n"
                "42,Current Engineer,loc-1,Berlin,Legacy Co,Engineering,"
                "https://legacy.test/jobs/42,2026-01-01\n",
                encoding="utf-8",
            )
            (processed / "job_details.csv").write_text(
                "title,location,company,department,link,mission,requirements,benefits,scrape_timestamp\n"
                "Current Engineer,Berlin,Legacy Co,Engineering,https://legacy.test/jobs/42,"
                "Build systems,Five years experience,Health plan,2026-01-01\n",
                encoding="utf-8",
            )
            (processed / "job_history.csv").write_text(
                "title,location,company,department,link,mission,requirements,benefits,"
                "scrape_timestamp,first_seen,last_seen,active\n"
                "Current Engineer,Berlin,Legacy Co,Engineering,https://legacy.test/jobs/42,"
                "Build systems,Five years experience,Health plan,2026-01-01,2025-12-01,2026-01-01,True\n"
                "Former Engineer,Munich,Legacy Co,Engineering,https://legacy.test/jobs/old,"
                "Old mission,,,2025-11-01,2025-10-01,2025-11-01,False\n",
                encoding="utf-8",
            )

            normalize_existing_provider(source_config, directory, "2026-01-02T00:00:00Z")

            with (processed / "jobs_latest.csv").open(newline="", encoding="utf-8") as handle:
                latest = list(csv.DictReader(handle))
            self.assertEqual(LATEST_FIELDS, tuple(latest[0].keys()))
            self.assertEqual("legacy:42", latest[0]["id"])
            self.assertNotIn("location_id", latest[0])

            with (processed / "job_history.csv").open(newline="", encoding="utf-8") as handle:
                history = list(csv.DictReader(handle))
            self.assertEqual(2, len(history))
            preserved = next(row for row in history if row["id"] == "legacy:42")
            self.assertEqual("2025-12-01", preserved["first_seen"])
            self.assertEqual("True", preserved["active"])
            self.assertEqual("Build systems", preserved["mission"])
            former = next(row for row in history if row["title"] == "Former Engineer")
            self.assertEqual("False", former["active"])
            self.assertTrue(former["id"].startswith("legacy:"))

    def test_existing_provider_recovers_native_identity_from_legacy_details(self):
        with tempfile.TemporaryDirectory() as directory:
            source_config = source(
                id="neura", company="NEURA Robotics",
                acquisition_mode="existing_provider", adapter="existing_provider",
            )
            processed = Path(directory) / "neura/processed"
            processed.mkdir(parents=True)
            (processed / "jobs_latest.csv").write_text(
                "title,location,company,department,link,scrape_timestamp\n"
                "Robotics Engineer,Munich,NEURA Robotics,AI,"
                "https://neura.test/offer/one,2026-01-01\n",
                encoding="utf-8",
            )
            (processed / "job_details.csv").write_text(
                "title,location,company,department,link,offer_uuid,mission,requirements,"
                "benefits,scrape_timestamp\n"
                "Robotics Engineer,Munich,NEURA Robotics,AI,https://neura.test/offer/one,"
                "offer-1,Build robots,Python experience,Health plan,2026-01-01\n",
                encoding="utf-8",
            )
            (processed / "job_history.csv").write_text(
                "title,location,company,department,link,mission,requirements,benefits,"
                "scrape_timestamp,first_seen,last_seen,active\n"
                "Robotics Engineer,Munich,NEURA Robotics,AI,https://neura.test/offer/one,"
                "Build robots,Python experience,Health plan,2026-01-01,2025-12-01,2026-01-01,True\n",
                encoding="utf-8",
            )

            normalize_existing_provider(source_config, directory, "2026-01-02T00:00:00Z")

            with (processed / "jobs_latest.csv").open(newline="", encoding="utf-8") as handle:
                latest = list(csv.DictReader(handle))
            with (processed / "job_changes.csv").open(newline="", encoding="utf-8") as handle:
                changes = list(csv.DictReader(handle))
            with (processed / "job_history.csv").open(newline="", encoding="utf-8") as handle:
                history = list(csv.DictReader(handle))

        self.assertEqual("neura:offer-1", latest[0]["id"])
        self.assertEqual("offer-1", latest[0]["source_job_id"])
        self.assertEqual([], changes)
        self.assertEqual(1, len(history))
        self.assertEqual("2025-12-01", history[0]["first_seen"])
        self.assertEqual("True", history[0]["active"])

    def test_reactivated_jobs_keep_history_and_report_reactivation(self):
        with tempfile.TemporaryDirectory() as directory:
            first = {
                "id": "demo:7", "source_id": "demo", "source_job_id": "7",
                "title": "Engineer", "location": "Berlin", "company": "Demo",
                "department": "Engineering", "link": "https://example.test/7",
            }
            replacement = dict(
                first,
                id="demo:8",
                source_job_id="8",
                title="Other Engineer",
                link="https://example.test/8",
            )
            process_success(directory, source(), AcquisitionResult([first]), "2026-01-01T00:00:00Z")
            process_success(directory, source(), AcquisitionResult([replacement]), "2026-01-02T00:00:00Z")
            process_success(directory, source(), AcquisitionResult([first]), "2026-01-03T00:00:00Z")

            processed = Path(directory) / "demo/processed"
            with (processed / "job_changes.csv").open(newline="", encoding="utf-8") as handle:
                changes = list(csv.DictReader(handle))
            with (processed / "job_history.csv").open(newline="", encoding="utf-8") as handle:
                history = {row["id"]: row for row in csv.DictReader(handle)}

        self.assertIn(("demo:7", "reactivated"), {
            (row["id"], row["change"]) for row in changes
        })
        self.assertEqual("2026-01-01", history["demo:7"]["first_seen"])
        self.assertEqual("True", history["demo:7"]["active"])
        self.assertEqual("False", history["demo:8"]["active"])

    def test_failure_preserves_prior_snapshot_and_reports_status(self):
        with tempfile.TemporaryDirectory() as directory:
            processed = Path(directory) / "demo/processed"
            processed.mkdir(parents=True)
            prior = {}
            for name in COMMON_OUTPUTS:
                target = processed / name
                target.write_bytes(f"prior-good-{name}\n".encode())
                prior[name] = target.read_bytes()
            metadata = run_source(source(), directory, fetch=lambda _url: (_ for _ in ()).throw(OSError("offline")))
            for name, content in prior.items():
                self.assertEqual(content, (processed / name).read_bytes())
            self.assertEqual("failed", metadata["status"])
            self.assertFalse(metadata["coverage_complete"])
            self.assertEqual(0, metadata["records_written"])


if __name__ == "__main__":
    unittest.main()
