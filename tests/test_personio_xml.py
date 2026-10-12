import csv
import json
import tempfile
import unittest
from pathlib import Path

from jobtracker.pipeline import run_source
from jobtracker.processing import COMMON_OUTPUTS, DETAIL_FIELDS, LATEST_FIELDS
from jobtracker.registry import get_source


PERSONIO_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<workzag-jobs>
  <position>
    <id>2817230</id>
    <subcompany>HyImpulse Technologies GmbH</subcompany>
    <office>Neuenstadt am Kocher</office>
    <department>Propulsion</department>
    <name>Chemical Engineer (m/f/d)</name>
    <jobDescriptions>
      <jobDescription>
        <name>Key Responsibilities</name>
        <value><![CDATA[<ul><li>Develop hybrid rocket motor propellants</li><li>Support engine tests</li></ul>]]></value>
      </jobDescription>
      <jobDescription>
        <name>Basic Qualification</name>
        <value><![CDATA[<ul><li>Degree in chemistry</li><li>Laboratory experience</li></ul>]]></value>
      </jobDescription>
      <jobDescription>
        <name>Desired Experience</name>
        <value><![CDATA[<p>Propulsion or aerospace experience</p>]]></value>
      </jobDescription>
      <jobDescription>
        <name>Benefits</name>
        <value><![CDATA[<ul><li>30 days of vacation</li><li>Flexible working hours</li></ul>]]></value>
      </jobDescription>
      <jobDescription>
        <name>Location</name>
        <value><![CDATA[Additional regional details that are not the job location]]></value>
      </jobDescription>
    </jobDescriptions>
  </position>
  <position>
    <id>2546581</id>
    <name>Software Engineer</name>
  </position>
</workzag-jobs>
"""

EXOLAUNCH_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<workzag-jobs>
  <position>
    <id>9001</id>
    <subcompany>Exolaunch GmbH</subcompany>
    <office>Berlin</office>
    <department>Engineering</department>
    <name>Launch Operations Engineer</name>
    <url>https://exolaunch.jobs.personio.com/job/9001</url>
    <jobDescriptions>
      <jobDescription>
        <name>Responsibilities</name>
        <value><![CDATA[<p>Coordinate launch campaign operations</p>]]></value>
      </jobDescription>
    </jobDescriptions>
  </position>
</workzag-jobs>
"""


class PersonioXMLTests(unittest.TestCase):
    def test_hyimpulse_acquires_structured_jobs_and_writes_canonical_outputs(self):
        source = get_source("hyimpulse")
        self.assertEqual("personio_xml", source["adapter"])

        with tempfile.TemporaryDirectory() as directory:
            metadata = run_source(
                source,
                directory,
                fetch=lambda url: PERSONIO_XML if url == source["adapter_config"]["url"] else b"",
            )
            processed = Path(directory) / "hyimpulse/processed"
            with (processed / "jobs_latest.csv").open(newline="", encoding="utf-8") as handle:
                latest = list(csv.DictReader(handle))
            with (processed / "job_details.csv").open(newline="", encoding="utf-8") as handle:
                details = list(csv.DictReader(handle))

        self.assertEqual("success", metadata["status"])
        self.assertEqual(LATEST_FIELDS, tuple(latest[0].keys()))
        self.assertEqual(DETAIL_FIELDS, tuple(details[0].keys()))
        self.assertEqual(2, len(latest))
        first = latest[0]
        self.assertEqual("hyimpulse:2817230", first["id"])
        self.assertEqual("2817230", first["source_job_id"])
        self.assertEqual("Chemical Engineer (m/f/d)", first["title"])
        self.assertEqual("Neuenstadt am Kocher", first["location"])
        self.assertEqual("HyImpulse Technologies GmbH", first["company"])
        self.assertEqual("Propulsion", first["department"])
        self.assertNotEqual("APPLY NOW", first["title"])
        self.assertEqual(
            "https://hyimpulse-technologies-gmbh.jobs.personio.com/job/2817230",
            first["link"],
        )

        detailed = details[0]
        self.assertIn("Develop hybrid rocket motor propellants", detailed["mission"])
        self.assertIn("Degree in chemistry", detailed["requirements"])
        self.assertIn("Propulsion or aerospace experience", detailed["requirements"])
        self.assertIn("30 days of vacation", detailed["benefits"])
        self.assertNotIn("<li>", detailed["mission"])
        self.assertNotIn("Additional regional details", detailed["mission"])

        optional = latest[1]
        self.assertEqual("", optional["location"])
        self.assertEqual("", optional["department"])
        self.assertEqual("", details[1]["mission"])
        self.assertEqual("", details[1]["requirements"])
        self.assertEqual("", details[1]["benefits"])

    def test_exolaunch_personio_source_still_uses_official_fields(self):
        source = get_source("exolaunch")

        with tempfile.TemporaryDirectory() as directory:
            run_source(source, directory, fetch=lambda _url: EXOLAUNCH_XML)
            processed = Path(directory) / "exolaunch/processed"
            with (processed / "jobs_latest.csv").open(newline="", encoding="utf-8") as handle:
                latest = list(csv.DictReader(handle))
            with (processed / "job_details.csv").open(newline="", encoding="utf-8") as handle:
                details = list(csv.DictReader(handle))

        self.assertEqual("exolaunch:9001", latest[0]["id"])
        self.assertEqual("Berlin", latest[0]["location"])
        self.assertEqual("Engineering", latest[0]["department"])
        self.assertEqual("Launch Operations Engineer", latest[0]["title"])
        self.assertIn("Coordinate launch campaign operations", details[0]["mission"])

    def test_incomplete_personio_position_preserves_existing_normalized_files(self):
        source = get_source("hyimpulse")
        incomplete_xml = b"""<workzag-jobs>
          <position><id>1</id><name>Real Engineer</name><url>https://jobs.test/1</url></position>
          <position><id>2</id><url>https://jobs.test/2</url></position>
        </workzag-jobs>"""

        with tempfile.TemporaryDirectory() as directory:
            processed = Path(directory) / "hyimpulse/processed"
            processed.mkdir(parents=True)
            previous = {}
            for filename in COMMON_OUTPUTS:
                target = processed / filename
                target.write_text(f"prior-good-{filename}\n", encoding="utf-8")
                previous[filename] = target.read_bytes()

            metadata = run_source(source, directory, fetch=lambda _url: incomplete_xml)

            self.assertEqual("incomplete", metadata["status"])
            self.assertFalse(metadata["coverage_complete"])
            for filename, content in previous.items():
                self.assertEqual(content, (processed / filename).read_bytes())

    def test_first_personio_success_resets_bad_html_link_history_once(self):
        source = get_source("hyimpulse")
        with tempfile.TemporaryDirectory() as directory:
            processed = Path(directory) / "hyimpulse/processed"
            processed.mkdir(parents=True)
            (processed / "acquisition.json").write_text(
                json.dumps({"adapter": "html_job_links"}), encoding="utf-8"
            )
            (processed / "jobs_latest.csv").write_text(
                "id,title,location,company,department,link,scrape_timestamp\n"
                "1,APPLY NOW,Unknown,HyImpulse,Unknown,"
                "https://legacy.test/job/1,2026-01-01\n",
                encoding="utf-8",
            )
            (processed / "job_details.csv").write_text(
                "id,title,location,company,department,link,mission,requirements,benefits,scrape_timestamp\n"
                "1,APPLY NOW,Unknown,HyImpulse,Unknown,https://legacy.test/job/1,,,,2026-01-01\n",
                encoding="utf-8",
            )
            (processed / "job_history.csv").write_text(
                "id,title,location,link,first_seen,last_seen,active\n"
                "1,APPLY NOW,Unknown,https://legacy.test/job/1,2026-01-01,2026-01-01,True\n",
                encoding="utf-8",
            )
            (processed / "job_changes.csv").write_text(
                "date,change_type,title,location,timestamp\n"
                "2026-01-01,NEW,APPLY NOW,Unknown,2026-01-01_00-00-00\n",
                encoding="utf-8",
            )

            run_source(source, directory, fetch=lambda _url: PERSONIO_XML)

            with (processed / "job_history.csv").open(newline="", encoding="utf-8") as handle:
                first_history = list(csv.DictReader(handle))
            self.assertEqual(
                {"Chemical Engineer (m/f/d)", "Software Engineer"},
                {row["title"] for row in first_history},
            )
            self.assertTrue(all(row["location"] != "Unknown" for row in first_history))
            self.assertTrue(all(row["department"] != "Unknown" for row in first_history))
            with (processed / "job_changes.csv").open(newline="", encoding="utf-8") as handle:
                first_changes = list(csv.DictReader(handle))
            self.assertTrue(all(row["change"] == "new" for row in first_changes))
            self.assertFalse(any(row["title"] == "APPLY NOW" for row in first_changes))

            first_history[0]["first_seen"] = "2000-01-01"
            with (processed / "job_history.csv").open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=first_history[0].keys())
                writer.writeheader()
                writer.writerows(first_history)
            run_source(source, directory, fetch=lambda _url: PERSONIO_XML)
            with (processed / "job_history.csv").open(newline="", encoding="utf-8") as handle:
                second_history = list(csv.DictReader(handle))

        self.assertIn("2000-01-01", {row["first_seen"] for row in second_history})


if __name__ == "__main__":
    unittest.main()
