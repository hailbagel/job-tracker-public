import csv
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, call

from scrapers.providers.neura_scraper import (
    NeuraScraper,
    NeuraSourceUnavailable,
    collect_jobs,
)


def response(payload, status=200):
    return Mock(status_code=status, json=Mock(return_value=payload))


def hit(identifier, title, location=None, department=None, **fields):
    document = {
        "offer_uuid": identifier,
        "title": title,
        "location": location or [],
        "company": "Neura Robotics",
        "department": department or [],
        "url": f"https://jobs.neura-robotics.com/offer/{identifier}",
    }
    document.update(fields)
    return {"document": document}


class NeuraTypesenseTest(unittest.TestCase):
    def test_parses_and_paginates_public_typesense_results(self):
        session = Mock()
        session.get.return_value = response({"key": "fixture-key"})
        session.post.side_effect = [
            response({"results": [{
                "found": 3,
                "hits": [
                    hit("one", "Controls Engineer", ["Riederich"], ["Software"]),
                    hit("two", "Robot Engineer"),
                ],
            }]}),
            response({"results": [{
                "found": 3,
                "hits": [hit("three", "AI Engineer", ["Munich"], ["AI"])],
            }]}),
        ]

        jobs = collect_jobs(session=session, timestamp="2026-09-30_00-00-00")

        self.assertEqual(3, len(jobs))
        self.assertEqual("Riederich", jobs[0]["location"])
        self.assertEqual("Software", jobs[0]["department"])
        self.assertEqual("Unknown", jobs[1]["location"])
        self.assertEqual([1, 2], [
            call.kwargs["json"]["searches"][0]["page"]
            for call in session.post.call_args_list
        ])
        session.get.assert_called_once()

    def test_preserves_rich_api_details_and_structured_fields(self):
        session = Mock()
        session.get.return_value = response({"key": "fixture-key"})
        session.post.return_value = response({"results": [{
            "found": 1,
            "hits": [hit(
                "rich", "Robotics Engineer", ["Munich", "Riederich"], ["AI"],
                description="Build cognitive robots",
                expectation="Python and robotics",
                benefits="30 days vacation",
                offering="Creative freedom",
                about="About NEURA",
                introduction="Join the team",
                additional="Start immediately",
                location_objects=[{"city": "Munich"}],
                work_mode=["hybrid"],
                salary={"currency": "EUR", "minimum": 70000},
                full_address="Munich, Germany",
                application_url="https://jobs.neura-robotics.com/apply/rich",
                company_url="https://neura-robotics.com",
                pitch_you_url="https://jobs.neura-robotics.com/pitch/rich",
            )],
        }]})

        jobs = collect_jobs(session=session, timestamp="2026-10-12_00-00-00")

        self.assertEqual("Build cognitive robots", jobs[0]["mission"])
        self.assertEqual("Python and robotics", jobs[0]["requirements"])
        self.assertEqual("30 days vacation", jobs[0]["benefits"])
        self.assertEqual('["Munich", "Riederich"]', jobs[0]["locations"])
        self.assertEqual('["hybrid"]', jobs[0]["work_mode"])
        self.assertIn('"minimum": 70000', jobs[0]["salary"])
        self.assertEqual(
            "https://jobs.neura-robotics.com/apply/rich",
            jobs[0]["application_url"],
        )
        requested = session.post.call_args.kwargs["json"]["searches"][0]["include_fields"]
        for field in ("description", "expectation", "offering", "about", "salary"):
            self.assertIn(field, requested)

    def test_scraper_writes_overview_and_complete_detail_contracts(self):
        session = Mock()
        session.get.return_value = response({"key": "fixture-key"})
        session.post.return_value = response({"results": [{
            "found": 1,
            "hits": [hit(
                "one", "Controls Engineer", ["Riederich"], ["Software"],
                description="Mission text", expectation="Requirements text",
                benefits="Benefits text", offering="Offering text",
                about="About text", introduction="Intro text",
                additional="Additional text", work_mode=["onsite"],
                salary={"currency": "EUR"},
                application_url="https://jobs.neura-robotics.com/apply/one",
            )],
        }]})
        with tempfile.TemporaryDirectory() as directory:
            NeuraScraper("neura").run(
                data_root=directory,
                session=session,
                timestamp="2026-10-12_00-00-00",
            )
            processed = Path(directory) / "neura/processed"
            with (processed / "jobs_latest.csv").open(newline="", encoding="utf-8") as handle:
                latest = list(csv.DictReader(handle))
            with (processed / "job_details.csv").open(newline="", encoding="utf-8") as handle:
                details = list(csv.DictReader(handle))

        self.assertEqual(1, len(latest))
        self.assertEqual(1, len(details))
        self.assertEqual('["onsite"]', latest[0]["work_mode"])
        self.assertEqual("Mission text", details[0]["description"])
        self.assertEqual("Requirements text", details[0]["requirements"])
        self.assertEqual("Offering text", details[0]["offering"])
        self.assertEqual("Additional text", details[0]["additional"])

    def test_malformed_acquisition_preserves_last_known_good_outputs(self):
        session = Mock()
        session.get.return_value = response({"key": "fixture-key"})
        session.post.return_value = response({"results": [{
            "found": 1, "hits": [{"document": {"offer_uuid": "broken"}}],
        }]})
        with tempfile.TemporaryDirectory() as directory:
            processed = Path(directory) / "neura/processed"
            processed.mkdir(parents=True)
            latest = processed / "jobs_latest.csv"
            details = processed / "job_details.csv"
            latest.write_text("last-known-good-latest\n", encoding="utf-8")
            details.write_text("last-known-good-details\n", encoding="utf-8")

            with self.assertRaises(NeuraSourceUnavailable):
                NeuraScraper("neura").run(data_root=directory, session=session)

            self.assertEqual("last-known-good-latest\n", latest.read_text())
            self.assertEqual("last-known-good-details\n", details.read_text())

    def test_incomplete_pagination_fails_closed(self):
        session = Mock()
        session.get.return_value = response({"key": "fixture-key"})
        session.post.side_effect = [
            response({"results": [{"found": 2, "hits": [hit("one", "Engineer")]}]}),
            response({"results": [{"found": 2, "hits": []}]}),
        ]

        with self.assertRaises(NeuraSourceUnavailable) as raised:
            collect_jobs(session=session)

        self.assertEqual(
            "upstream_incomplete_response", raised.exception.classification
        )


if __name__ == "__main__":
    unittest.main()
