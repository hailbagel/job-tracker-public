import unittest
from unittest.mock import Mock, call

from scrapers.providers.neura_scraper import (
    NeuraSourceUnavailable,
    collect_jobs,
)


def response(payload, status=200):
    return Mock(status_code=status, json=Mock(return_value=payload))


def hit(identifier, title, location=None, department=None):
    return {
        "document": {
            "offer_uuid": identifier,
            "title": title,
            "location": location or [],
            "company": "Neura Robotics",
            "department": department or [],
            "url": f"https://jobs.neura-robotics.com/offer/{identifier}",
        }
    }


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
