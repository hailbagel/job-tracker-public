import csv
import json
import os
import tempfile
import unittest
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

    @patch("scrapers.providers.spacex_scraper._fetch_jobs")
    def test_complete_api_content_writes_identity_details_and_coverage(self, fetch):
        fetch.return_value = Response([listing()])
        SpaceXScraper("spacex").run()
        with Path("data/spacex/processed/jobs_latest.csv").open(newline="", encoding="utf-8") as handle:
            latest = list(csv.DictReader(handle))
        with Path("data/spacex/processed/job_details.csv").open(newline="", encoding="utf-8") as handle:
            details = list(csv.DictReader(handle))
        acquisition = json.loads(Path("data/spacex/processed/acquisition.json").read_text(encoding="utf-8"))
        self.assertEqual("55", latest[0]["id"])
        self.assertEqual("DUPLICATE-OK", latest[0]["requisition_id"])
        self.assertIn("BASIC QUALIFICATIONS", details[0]["requirements"])
        self.assertTrue(acquisition["coverage_complete"])
        self.assertEqual(1, acquisition["records_written"])

    @patch("scrapers.providers.spacex_scraper._fetch_jobs")
    def test_nonempty_incomplete_api_does_not_replace_prior_good_snapshot(self, fetch):
        target = Path("data/spacex/processed/jobs_latest.csv")
        target.parent.mkdir(parents=True)
        target.write_bytes(b"prior-good-bytes\n")
        invalid = listing()
        invalid["id"] = None
        fetch.return_value = Response([listing(), invalid])
        with self.assertRaises(SystemExit):
            SpaceXScraper("spacex").run()
        self.assertEqual(b"prior-good-bytes\n", target.read_bytes())


if __name__ == "__main__":
    unittest.main()
