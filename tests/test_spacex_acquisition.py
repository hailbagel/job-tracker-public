import csv
import json
import os
import tempfile
import unittest
from datetime import datetime as real_datetime
from pathlib import Path
from unittest.mock import patch

from scrapers.providers.spacex_scraper import SpaceXScraper


class Response:
    status_code = 200
    text = ""

    def __init__(self, jobs):
        self.jobs = jobs

    def json(self):
        return {"jobs": self.jobs}


def listing(job_id="55"):
    return {
        "id": job_id,
        "title": "Construction Project Manager",
        "location": {"name": "Pecan Island, Louisiana"},
        "absolute_url": f"https://example.test/{job_id}",
        "requisition_id": "DUPLICATE-OK",
        "first_published": "2026-01-01",
        "updated_at": "2026-01-02",
        "metadata": [{"name": "Discipline", "value": "Facilities"}],
        "content": "<h3>BASIC QUALIFICATIONS:</h3><p>5 years construction.</p><h3>PREFERRED QUALIFICATIONS:</h3><p>Bluebeam.</p>",
    }


class SpaceXAcquisitionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.previous_cwd = os.getcwd()
        os.chdir(self.temp.name)

    def tearDown(self):
        os.chdir(self.previous_cwd)
        self.temp.cleanup()

    def _write_stale_bootstrap(self):
        path = Path("data/spacex/processed/acquisition.json")
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({
            "coverage_complete": False, "records_written": 0, "observed_at": None,
            "data_changed_at": None, "data_hash": None,
        }), encoding="utf-8")

    def _run_at(self, fetch, jobs, moment):
        fetch.return_value = Response(jobs)
        with patch("scrapers.providers.spacex_scraper.datetime") as clock:
            clock.now.return_value = real_datetime.fromisoformat(moment.replace("Z", "+00:00"))
            SpaceXScraper("spacex").run()

    @patch("scrapers.providers.spacex_scraper._fetch_jobs")
    def test_complete_api_content_writes_identity_details_and_coverage(self, fetch):
        self._write_stale_bootstrap()
        self._run_at(fetch, [listing(), listing("56")], "2026-09-23T10:00:00Z")
        with Path("data/spacex/processed/jobs_latest.csv").open(newline="", encoding="utf-8") as handle:
            latest = list(csv.DictReader(handle))
        with Path("data/spacex/processed/job_details.csv").open(newline="", encoding="utf-8") as handle:
            details = list(csv.DictReader(handle))
        acquisition = json.loads(Path("data/spacex/processed/acquisition.json").read_text(encoding="utf-8"))
        self.assertEqual("55", latest[0]["id"])
        self.assertEqual("DUPLICATE-OK", latest[0]["requisition_id"])
        self.assertIn("BASIC QUALIFICATIONS", details[0]["requirements"])
        self.assertEqual("success", acquisition["status"])
        self.assertTrue(acquisition["coverage_complete"])
        self.assertEqual(len(latest), acquisition["records_written"])
        self.assertEqual("2026-09-23T10:00:00Z", acquisition["observed_at"])
        self.assertEqual(acquisition["observed_at"], acquisition["data_changed_at"])
        self.assertIsNotNone(acquisition["data_hash"])

    @patch("scrapers.providers.spacex_scraper._fetch_jobs")
    def test_unchanged_data_preserves_change_time_and_changed_data_advances_it(self, fetch):
        self._run_at(fetch, [listing()], "2026-09-23T10:00:00Z")
        first = json.loads(Path("data/spacex/processed/acquisition.json").read_text(encoding="utf-8"))

        self._run_at(fetch, [listing()], "2026-09-23T11:00:00Z")
        unchanged = json.loads(Path("data/spacex/processed/acquisition.json").read_text(encoding="utf-8"))
        self.assertEqual("2026-09-23T11:00:00Z", unchanged["observed_at"])
        self.assertEqual(first["data_changed_at"], unchanged["data_changed_at"])
        self.assertEqual(first["data_hash"], unchanged["data_hash"])

        changed = listing()
        changed["title"] = "Senior Construction Project Manager"
        self._run_at(fetch, [changed], "2026-09-23T12:00:00Z")
        updated = json.loads(Path("data/spacex/processed/acquisition.json").read_text(encoding="utf-8"))
        self.assertEqual("2026-09-23T12:00:00Z", updated["observed_at"])
        self.assertEqual(updated["observed_at"], updated["data_changed_at"])
        self.assertNotEqual(first["data_hash"], updated["data_hash"])

    @patch("scrapers.providers.spacex_scraper._fetch_jobs")
    def test_nonempty_incomplete_api_does_not_replace_prior_good_snapshot(self, fetch):
        self._run_at(fetch, [listing()], "2026-09-23T10:00:00Z")
        target = Path("data/spacex/processed/jobs_latest.csv")
        prior_bytes = target.read_bytes()
        prior = json.loads(Path("data/spacex/processed/acquisition.json").read_text(encoding="utf-8"))
        invalid = listing()
        invalid["id"] = None
        fetch.return_value = Response([listing(), invalid])
        with patch("scrapers.providers.spacex_scraper.datetime") as clock:
            clock.now.return_value = real_datetime.fromisoformat("2026-09-23T11:00:00+00:00")
            with self.assertRaises(SystemExit):
                SpaceXScraper("spacex").run()
        failed = json.loads(Path("data/spacex/processed/acquisition.json").read_text(encoding="utf-8"))
        self.assertEqual(prior_bytes, target.read_bytes())
        self.assertEqual("incomplete", failed["status"])
        self.assertFalse(failed["coverage_complete"])
        self.assertEqual(0, failed["records_written"])
        self.assertEqual(2, failed["source_records"])
        self.assertEqual("2026-09-23T11:00:00Z", failed["observed_at"])
        self.assertEqual(prior["data_changed_at"], failed["data_changed_at"])
        self.assertEqual(prior["data_hash"], failed["data_hash"])


if __name__ == "__main__":
    unittest.main()
