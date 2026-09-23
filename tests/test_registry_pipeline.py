import csv
import json
import tempfile
import unittest
from pathlib import Path

from jobtracker.acquisition import AcquisitionResult, acquire
from jobtracker.pipeline import run_source
from jobtracker.processing import COMMON_OUTPUTS, process_success
from jobtracker.registry import RegistryError, load_registry


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

    def test_failure_preserves_prior_snapshot_and_reports_status(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "demo/processed/jobs_latest.csv"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"prior-good\n")
            metadata = run_source(source(), directory, fetch=lambda _url: (_ for _ in ()).throw(OSError("offline")))
            self.assertEqual(b"prior-good\n", target.read_bytes())
            self.assertEqual("failed", metadata["status"])
            self.assertFalse(metadata["coverage_complete"])
            self.assertEqual(0, metadata["records_written"])


if __name__ == "__main__":
    unittest.main()
