"""Regression tests for history rows no longer present in the current snapshot."""
import csv
import tempfile
import unittest
from pathlib import Path

from jobtracker.acquisition import AcquisitionResult
from jobtracker.processing import process_success


class HistoricalActiveInvariantTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.source = {"id": "spacex", "company": "SpaceX"}
        self.processed = self.root / "spacex" / "processed"

    def tearDown(self):
        self.directory.cleanup()

    @staticmethod
    def job(job_id):
        return {
            "id": f"spacex:{job_id}",
            "source_id": "spacex",
            "source_job_id": str(job_id),
            "title": f"Engineer {job_id}",
            "location": "Starbase, TX",
            "company": "SpaceX",
            "department": "Engineering",
            "link": f"https://example.test/spacex/jobs/{job_id}",
            "mission": "Build spacecraft",
        }

    def publish(self, job_ids, date):
        process_success(
            self.root,
            self.source,
            AcquisitionResult([self.job(identifier) for identifier in job_ids]),
            observed_at=f"{date}T12:00:00Z",
            write_status=False,
            preserve_change_history=True,
        )

    def rows(self, name):
        with (self.processed / name).open(newline="", encoding="utf-8") as stream:
            return list(csv.DictReader(stream))

    def write_rows(self, name, rows):
        path = self.processed / name
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def orphan_fixture(self):
        self.publish([11, 12], "2026-10-01")
        self.publish([11], "2026-10-02")
        before = self.rows("job_history.csv")
        former = next(row for row in before if row["id"] == "spacex:12")
        self.assertEqual("False", former["active"])
        self.assertEqual("2026-10-01", former["last_seen"])
        # Reproduce production defect: a retained history record marked active
        # even though it has been absent from earlier current snapshots.
        former["active"] = "True"
        self.write_rows("job_history.csv", before)

    def test_orphan_is_closed_without_erasing_history_or_inventing_removal(self):
        self.orphan_fixture()
        previous_changes = self.rows("job_changes.csv")
        self.publish([11], "2026-10-03")
        history = {row["id"]: row for row in self.rows("job_history.csv")}
        current = {row["id"] for row in self.rows("jobs_latest.csv")}
        active = {identifier for identifier, row in history.items() if row["active"] == "True"}

        self.assertEqual({"spacex:11"}, current)
        self.assertEqual(current, active)
        self.assertEqual(2, len(history))
        self.assertEqual("False", history["spacex:12"]["active"])
        self.assertEqual("2026-10-01", history["spacex:12"]["last_seen"])
        self.assertEqual(previous_changes, self.rows("job_changes.csv"))

        # A second unchanged acquisition must not create extra removals.
        self.publish([11], "2026-10-04")
        self.assertEqual(previous_changes, self.rows("job_changes.csv"))
        self.assertEqual(2, len(self.rows("job_history.csv")))

    def test_reappearance_is_recorded_as_reactivation(self):
        self.orphan_fixture()
        self.publish([11], "2026-10-03")
        self.publish([11, 12], "2026-10-04")
        history = {row["id"]: row for row in self.rows("job_history.csv")}
        current = {row["id"] for row in self.rows("jobs_latest.csv")}
        active = {identifier for identifier, row in history.items() if row["active"] == "True"}
        changes = self.rows("job_changes.csv")

        self.assertEqual(current, active)
        self.assertEqual(2, len(history))
        self.assertEqual("2026-10-01", history["spacex:12"]["first_seen"])
        self.assertEqual("2026-10-04", history["spacex:12"]["last_seen"])
        self.assertEqual(
            1,
            sum(row["id"] == "spacex:12" and row["change"] == "reactivated" for row in changes),
        )


if __name__ == "__main__":
    unittest.main()
