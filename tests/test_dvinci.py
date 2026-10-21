import csv
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path

from jobtracker.acquisition import acquire
from jobtracker.pipeline import run_source
from jobtracker.processing import COMMON_OUTPUTS, DETAIL_FIELDS, LATEST_FIELDS
from jobtracker.registry import get_source


FEED_URL = "https://career.sms-group.com/jobPublication/list.json"
SITEMAP_URL = "https://career.sms-group.com/sitemap.xml"


def source_for_test():
    source = dict(get_source("sms-group"))
    source["acquisition_mode"] = "api"
    return source


def publication(
    publication_id,
    opening_id,
    language,
    title,
    *,
    department=None,
    company="SMS group GmbH",
    location="Moenchengladbach",
    reference=None,
    introduction="",
    tasks="",
    profile="",
    we_offer="",
):
    return {
        "id": publication_id,
        "language": language,
        "position": title,
        "jobPublicationURL": (
            f"https://career.sms-group.com/{language}/jobs/"
            f"{publication_id}/{publication_id}-job"
        ),
        "introduction": introduction,
        "tasks": tasks,
        "profile": profile,
        "weOffer": we_offer,
        "jobOpening": {
            "id": opening_id,
            "reference": reference,
            "company": {"name": company},
            "location": location,
            "department": {"name": department} if department else None,
        },
    }


def fixture_records():
    return [
        publication(
            101,
            501,
            "de",
            "Projektleiter Anlagenbau",
            company="SMS group GmbH",
            location="Moenchengladbach",
            reference="SM-501",
            introduction="<p>Planung &amp; Umsetzung</p>",
            tasks="<ul><li>Leite Anlagenprojekte.</li></ul>",
            profile="<p>Erfahrung im Anlagenbau</p>",
            we_offer="<p>Flexible Arbeitszeiten</p>",
        ),
        publication(
            102,
            501,
            "en",
            "Plant Project Manager",
            department="Project Engineering",
            company="SMS group S.p.A.",
            location="Tarcento",
            reference="SM-501",
            introduction="<p>Build reliable plants.</p>",
            tasks="<p>Lead industrial projects &amp; commissioning.</p>",
            profile="<p>Plant engineering experience.</p>",
            we_offer="<p>Flexible hours.</p>",
        ),
        publication(
            103,
            502,
            "de",
            "Instandhaltungstechniker",
            location="Duisburg",
        ),
    ]


def sitemap_for(records):
    locations = "".join(
        f"<url><loc>{item['jobPublicationURL']}</loc></url>"
        for item in records
    )
    return (
        "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
        f"{locations}</urlset>"
    ).encode()


def fetch_for(records, sitemap=None):
    payloads = {
        FEED_URL: json.dumps(records).encode(),
        SITEMAP_URL: sitemap if sitemap is not None else sitemap_for(records),
    }
    requested = []

    def fetch(url):
        requested.append(url)
        return payloads[url]

    return fetch, requested


class DvinciAcquisitionTests(unittest.TestCase):
    def test_complete_unpaged_feed_matches_sitemap_and_deduplicates_locales(self):
        records = fixture_records()
        fetch, requested = fetch_for(records)

        result = acquire(source_for_test(), fetch=fetch)

        self.assertEqual("success", result.status)
        self.assertTrue(result.coverage_complete)
        self.assertEqual([FEED_URL, SITEMAP_URL], requested)
        self.assertEqual(["501", "502"], [
            job["source_job_id"] for job in result.jobs
        ])
        selected = result.jobs[0]
        self.assertEqual("sms-group:501", selected["id"])
        self.assertEqual("Plant Project Manager", selected["title"])
        self.assertEqual(
            "https://career.sms-group.com/en/jobs/102/102-job",
            selected["link"],
        )
        self.assertEqual("SMS group S.p.A.", selected["company"])
        self.assertEqual("Tarcento", selected["location"])
        self.assertEqual("Project Engineering", selected["department"])
        self.assertEqual("SM-501", selected["requisition_id"])
        self.assertIn("Build reliable plants.", selected["mission"])
        self.assertIn("Lead industrial projects & commissioning.", selected["mission"])
        self.assertEqual("Plant engineering experience.", selected["requirements"])
        self.assertEqual("Flexible hours.", selected["benefits"])
        self.assertEqual("", result.jobs[1]["mission"])
        self.assertEqual("", result.jobs[1]["requirements"])
        self.assertEqual("", result.jobs[1]["benefits"])

    def test_registry_keeps_sms_manual_until_production_bootstrap_review(self):
        source = get_source("sms-group")
        calls = []

        result = acquire(source, fetch=lambda url: calls.append(url))

        self.assertEqual("dvinci", source["adapter"])
        self.assertEqual("manual_discovery", source["acquisition_mode"])
        self.assertEqual("Industrial/Plant Engineering", source["sector"])
        self.assertNotIn("patrick", source["tags"])
        self.assertEqual("manual_discovery", result.status)
        self.assertFalse(result.coverage_complete)
        self.assertEqual([], calls)

    def test_partial_valid_listing_and_bad_sitemap_fail_closed(self):
        records = fixture_records()
        partial_fetch, _ = fetch_for(records[:-1], sitemap=sitemap_for(records))
        partial = acquire(source_for_test(), fetch=partial_fetch)
        self.assertEqual("incomplete", partial.status)
        self.assertFalse(partial.coverage_complete)
        self.assertIn("do not match", partial.reason)
        self.assertEqual([], partial.jobs)

        duplicate_sitemap_fetch, _ = fetch_for(
            records, sitemap=sitemap_for(records + [records[0]])
        )
        malformed = acquire(source_for_test(), fetch=duplicate_sitemap_fetch)
        self.assertEqual("incomplete", malformed.status)
        self.assertFalse(malformed.coverage_complete)
        self.assertIn("do not match", malformed.reason)

    def test_empty_malformed_duplicate_and_noncanonical_records_are_incomplete(self):
        empty_fetch, _ = fetch_for([], sitemap=sitemap_for([]))
        empty = acquire(source_for_test(), fetch=empty_fetch)
        self.assertEqual("incomplete", empty.status)
        self.assertIn("no publication array", empty.reason)

        def invalid_json(url):
            if url == FEED_URL:
                return b'{"not": "an array"}'
            return sitemap_for(fixture_records())

        malformed = acquire(source_for_test(), fetch=invalid_json)
        self.assertEqual("incomplete", malformed.status)
        self.assertFalse(malformed.coverage_complete)

        def invalid_json_syntax(url):
            return b"{" if url == FEED_URL else sitemap_for(fixture_records())

        failed_json = acquire(source_for_test(), fetch=invalid_json_syntax)
        self.assertEqual("failed", failed_json.status)
        self.assertIn("JSONDecodeError", failed_json.reason)

        records = fixture_records()
        records.append(dict(records[0]))
        duplicate_fetch, _ = fetch_for(records)
        duplicate = acquire(source_for_test(), fetch=duplicate_fetch)
        self.assertEqual("incomplete", duplicate.status)
        self.assertIn("duplicate", duplicate.reason)

        records = fixture_records()
        records[0] = dict(records[0], jobPublicationURL="https://elsewhere.test/job/101")
        invalid_link_fetch, _ = fetch_for(records)
        invalid_link = acquire(source_for_test(), fetch=invalid_link_fetch)
        self.assertEqual("incomplete", invalid_link.status)
        self.assertIn("canonical URL", invalid_link.reason)

    def test_http_401_403_and_429_from_each_endpoint_are_failures(self):
        records = fixture_records()
        for endpoint in (FEED_URL, SITEMAP_URL):
            for status_code in (401, 403, 429):
                with self.subTest(endpoint=endpoint, status=status_code):
                    def fetch(url, endpoint=endpoint, status_code=status_code):
                        if url == endpoint:
                            error = urllib.error.HTTPError(
                                url, status_code, "blocked", None, None
                            )
                            error.close()
                            raise error
                        return (
                            json.dumps(records).encode()
                            if url == FEED_URL
                            else sitemap_for(records)
                        )

                    result = acquire(source_for_test(), fetch=fetch)
                    self.assertEqual("failed", result.status)
                    self.assertFalse(result.coverage_complete)
                    self.assertIn(str(status_code), result.reason)

    def test_repeat_collection_is_stable_and_preserves_history_on_reactivation(self):
        records = fixture_records()
        with tempfile.TemporaryDirectory() as directory:
            first_fetch, _ = fetch_for(records)
            first = run_source(source_for_test(), directory, fetch=first_fetch)
            repeat_fetch, _ = fetch_for(records)
            repeat = run_source(source_for_test(), directory, fetch=repeat_fetch)

            processed = Path(directory) / "sms-group" / "processed"
            with (processed / "jobs_latest.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                latest = list(csv.DictReader(handle))
            with (processed / "job_details.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                details = list(csv.DictReader(handle))
            with (processed / "job_history.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                history = list(csv.DictReader(handle))
            with (processed / "job_changes.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                changes = list(csv.DictReader(handle))

            self.assertEqual("success", first["status"])
            self.assertEqual("success", repeat["status"])
            self.assertEqual(2, repeat["records_written"])
            self.assertEqual(LATEST_FIELDS, tuple(latest[0]))
            self.assertEqual(DETAIL_FIELDS, tuple(details[0]))
            self.assertEqual({"sms-group:501", "sms-group:502"}, {
                row["id"] for row in latest
            })
            self.assertEqual(2, len(history))
            self.assertEqual({"True"}, {row["active"] for row in history})
            self.assertEqual(
                {row["id"] for row in latest},
                {row["id"] for row in history if row["active"] == "True"},
            )
            self.assertEqual([], changes)

            removed_fetch, _ = fetch_for(records[1:2])
            run_source(source_for_test(), directory, fetch=removed_fetch)
            reactivated_fetch, _ = fetch_for(records)
            run_source(source_for_test(), directory, fetch=reactivated_fetch)
            with (processed / "job_history.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                history_after_reactivation = list(csv.DictReader(handle))
            with (processed / "job_changes.csv").open(
                newline="", encoding="utf-8"
            ) as handle:
                changes_after_reactivation = list(csv.DictReader(handle))

            self.assertEqual(2, len(history_after_reactivation))
            self.assertEqual({"True"}, {
                row["active"] for row in history_after_reactivation
            })
            self.assertEqual(
                {row["first_seen"] for row in history},
                {row["first_seen"] for row in history_after_reactivation},
            )
            self.assertEqual(
                1,
                sum(
                    row["id"] == "sms-group:502"
                    and row["change"] == "reactivated"
                    for row in changes_after_reactivation
                ),
            )

    def test_incomplete_refresh_preserves_previous_good_outputs(self):
        records = fixture_records()
        with tempfile.TemporaryDirectory() as directory:
            good_fetch, _ = fetch_for(records)
            run_source(source_for_test(), directory, fetch=good_fetch)
            processed = Path(directory) / "sms-group" / "processed"
            previous = {
                name: (processed / name).read_bytes()
                for name in COMMON_OUTPUTS
            }

            partial_fetch, _ = fetch_for(records[:-1], sitemap=sitemap_for(records))
            metadata = run_source(
                source_for_test(), directory, fetch=partial_fetch
            )

            self.assertEqual("incomplete", metadata["status"])
            self.assertFalse(metadata["coverage_complete"])
            self.assertEqual(0, metadata["records_written"])
            for name, content in previous.items():
                self.assertEqual(content, (processed / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
