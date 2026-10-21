import csv
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from jobtracker.pipeline import run_source
from jobtracker.processing import CHANGE_FIELDS, DETAIL_FIELDS, LATEST_FIELDS
from jobtracker.registry import get_source
from scripts import audit_public_data as audit


class NeuraAuxiliaryAuditTest(unittest.TestCase):
    def test_legacy_snapshot_does_not_require_count_parity(self):
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent
        ) as directory:
            auxiliary_path = Path(directory) / "jobs_structured.csv"
            current_path = Path(directory) / "jobs_latest.csv"
            with auxiliary_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(("title", "location", "company", "department"))
                writer.writerow(("Legacy role", "Metzingen", "Neura Robotics", "AI"))
            with current_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(("title", "link"))
                writer.writerow(("Current role 1", "https://example.test/1"))
                writer.writerow(("Current role 2", "https://example.test/2"))

            message = audit.summarize_neura_auxiliary(
                auxiliary_path, current_path
            )

        self.assertIn("1 entries", message)
        self.assertIn("2 current entries", message)
        self.assertIn("Count parity is not expected", message)

    def test_legacy_snapshot_requires_its_display_fields(self):
        with tempfile.TemporaryDirectory(
            dir=Path(__file__).resolve().parent
        ) as directory:
            auxiliary_path = Path(directory) / "jobs_structured.csv"
            current_path = Path(directory) / "jobs_latest.csv"
            auxiliary_path.write_text("title,location\nRole,Metzingen\n", encoding="utf-8")
            current_path.write_text(
                "title,link\nCurrent role,https://example.test/1\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(ValueError, "unexpected CSV columns"):
                audit.summarize_neura_auxiliary(auxiliary_path, current_path)


class SmsFullAuditFixtureTest(unittest.TestCase):
    def _write_csv(self, path, fields, rows=()):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)

    def _feed_files(self, root, area):
        directory = root / "data" / area / "processed"
        directory.mkdir(parents=True, exist_ok=True)
        self._write_csv(directory / "patrick_targets.csv", ("job_id", "title"))
        (directory / "patrick_targets.json").write_text(
            json.dumps({
                "rankings": [],
                "metadata": {
                    "counts": {"scanned": 0},
                    "source_coverage": [],
                },
            }),
            encoding="utf-8",
        )
        (directory / "patrick_targets.md").write_text(
            "# Fixture feed\n\nScanned: 0\n", encoding="utf-8"
        )

    def test_sms_outputs_pass_full_audit_with_exact_tracked_path_set(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sms = dict(get_source("sms-group"))
            spacex = {
                "id": "spacex",
                "company": "SpaceX",
                "careers_url": "https://www.spacex.com/careers/jobs/",
                "country": "United States",
                "region": "International",
                "sector": "Space/Rocket",
                "acquisition_mode": "existing_provider",
                "enabled": True,
                "priority": "A",
                "tags": [],
                "adapter": "existing_provider",
            }
            (root / "configs").mkdir()
            (root / "configs/sources.json").write_text(
                json.dumps({"schema_version": 1, "sources": [sms, spacex]}),
                encoding="utf-8",
            )

            record = {
                "id": 701,
                "language": "en",
                "position": "Plant Reliability Engineer",
                "jobPublicationURL": (
                    "https://career.sms-group.com/en/jobs/701/"
                    "plant-reliability-engineer"
                ),
                "introduction": "<p>Maintain reliable plants.</p>",
                "tasks": "<p>Support operations.</p>",
                "profile": "<p>Engineering experience.</p>",
                "weOffer": "<p>Flexible work.</p>",
                "jobOpening": {
                    "id": 9001,
                    "reference": "SMS-9001",
                    "company": {"name": "SMS group GmbH"},
                    "location": "Duesseldorf",
                    "department": {"name": "Plant Engineering"},
                },
            }
            feed = json.dumps([record]).encode()
            sitemap = (
                "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
                "<url><loc>https://career.sms-group.com/en/jobs/701/"
                "plant-reliability-engineer</loc></url></urlset>"
            ).encode()

            def fetch(url):
                if url == sms["adapter_config"]["url"]:
                    return feed
                if url == sms["adapter_config"]["sitemap_url"]:
                    return sitemap
                raise AssertionError(f"Unexpected URL: {url}")

            with patch.dict(
                "os.environ", {"JOB_TRACKER_ENABLE_SMS_GROUP": "1"}
            ):
                sms_metadata = run_source(sms, root / "data", fetch=fetch)

            spacex_dir = root / "data/spacex/processed"
            spacex_dir.mkdir(parents=True)
            for name in audit.OUTPUTS:
                if name == "jobs_latest.csv":
                    fields = LATEST_FIELDS
                elif name == "job_details.csv":
                    fields = DETAIL_FIELDS
                elif name == "job_history.csv":
                    fields = DETAIL_FIELDS + ("first_seen", "last_seen", "active")
                elif name == "job_changes.csv":
                    fields = CHANGE_FIELDS
                elif name == "department_summary.csv":
                    fields = ("department", "count")
                else:
                    fields = ("location", "count")
                self._write_csv(spacex_dir / name, fields)
            (spacex_dir / "acquisition.json").write_text(
                '{"status":"incomplete","coverage_complete":false,'
                '"records_written":0}\n',
                encoding="utf-8",
            )

            neura_dir = root / "data/neura/processed"
            self._write_csv(
                neura_dir / "jobs_structured.csv",
                ("title", "location", "company", "department"),
            )
            self._feed_files(root, "patrick")
            self._feed_files(root, "spacex")
            spacex_status = {
                "source_id": "spacex",
                "company": "SpaceX",
                "acquisition_mode": "existing_provider",
                "adapter": "existing_provider",
                "status": "incomplete",
                "coverage_complete": False,
                "records_written": 0,
                "reason": "fixture unavailable",
                "attempted": True,
            }
            (root / "data/source_status.json").write_text(
                json.dumps({
                    "schema_version": 1,
                    "publication": {
                        "attempted_sources": ["sms-group", "spacex"],
                        "successful_sources": ["sms-group"],
                        "failed_or_incomplete_sources": ["spacex"],
                        "published_feed_contributors": [],
                        "patrick_feed_coverage_complete": True,
                    },
                    "sources": [dict(sms_metadata, attempted=True), spacex_status],
                }),
                encoding="utf-8",
            )

            tracked_paths = "\n".join(
                path.relative_to(root).as_posix()
                for path in sorted((root / "data").rglob("*"))
                if path.is_file()
            )

            audit.failures.clear()
            audit.warnings.clear()
            success_output = io.StringIO()
            with patch.object(audit, "ROOT", root), \
                    patch.object(audit, "DATA", root / "data"), \
                    patch.object(
                        audit.subprocess, "check_output",
                        return_value=tracked_paths,
                    ), \
                    patch.object(
                        audit, "summarize_neura_auxiliary",
                        return_value="NEURA fixture",
                    ), \
                    redirect_stdout(success_output):
                success_status = audit.main()
            self.assertEqual(0, success_status, success_output.getvalue())
            self.assertEqual([], audit.failures)
            self.assertTrue(any(
                "sms-group: current=1 detail=1 history=1" in line
                for line in success_output.getvalue().splitlines()
            ))
            self.assertIn("tracked data files:", success_output.getvalue())

            processed = root / "data/sms-group/processed"
            bootstrap_fields = {
                "jobs_latest.csv": LATEST_FIELDS,
                "job_details.csv": DETAIL_FIELDS,
                "job_history.csv": DETAIL_FIELDS + ("first_seen", "last_seen", "active"),
                "job_changes.csv": CHANGE_FIELDS,
                "department_summary.csv": ("department", "count"),
                "location_summary.csv": ("location", "count"),
            }
            for name, fields in bootstrap_fields.items():
                self._write_csv(processed / name, fields)
            (processed / "acquisition.json").write_text(
                json.dumps({
                    "source_id": "sms-group",
                    "status": "incomplete",
                    "coverage_complete": False,
                    "records_written": 0,
                    "publication_status": "awaiting_first_verified_production_run",
                }),
                encoding="utf-8",
            )
            status_document = json.loads(
                (root / "data/source_status.json").read_text(encoding="utf-8")
            )
            sms_status = next(
                row for row in status_document["sources"]
                if row["source_id"] == "sms-group"
            )
            sms_status.update({
                "attempted": False,
                "status": "incomplete",
                "coverage_complete": False,
                "records_written": 0,
                "reason": "Host opt-in is disabled",
                "publication_status": "awaiting_first_verified_production_run",
            })
            status_document["publication"].update({
                "attempted_sources": ["spacex"],
                "successful_sources": [],
                "failed_or_incomplete_sources": ["sms-group", "spacex"],
            })
            (root / "data/source_status.json").write_text(
                json.dumps(status_document), encoding="utf-8"
            )
            audit.failures.clear()
            audit.warnings.clear()
            bootstrap_output = io.StringIO()
            with patch.object(audit, "ROOT", root), \
                    patch.object(audit, "DATA", root / "data"), \
                    patch.object(
                        audit.subprocess, "check_output",
                        return_value=tracked_paths,
                    ), \
                    patch.object(
                        audit, "summarize_neura_auxiliary",
                        return_value="NEURA fixture",
                    ), \
                    redirect_stdout(bootstrap_output):
                bootstrap_status = audit.main()

        self.assertEqual(0, bootstrap_status, bootstrap_output.getvalue())
        self.assertEqual([], audit.failures)
        self.assertIn("sms-group: failed collection", bootstrap_output.getvalue())


if __name__ == "__main__":
    unittest.main()
