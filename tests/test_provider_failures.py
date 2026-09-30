import unittest
from unittest.mock import Mock, patch

from scrapers.providers.jacobs_scraper import JacobsScraper, JacobsSourceUnavailable
from scrapers.providers.tesla_scraper import TeslaScraper, TeslaSourceUnavailable


class TeslaFailureClassificationTest(unittest.TestCase):
    @patch("scrapers.providers.tesla_scraper.os.makedirs")
    @patch("scrapers.providers.tesla_scraper._fetch_state_json")
    def test_http_403_is_classified_as_upstream_access_denied(
        self, fetch_state_json, _makedirs
    ):
        fetch_state_json.return_value = Mock(status_code=403)

        with self.assertRaises(TeslaSourceUnavailable) as raised:
            TeslaScraper("tesla").run()

        self.assertEqual(raised.exception.classification, "upstream_access_denied")
        self.assertIn("HTTP 403", str(raised.exception))
        fetch_state_json.assert_called_once()


class JacobsFailureClassificationTest(unittest.TestCase):
    @patch("scrapers.providers.jacobs_scraper._fetch_search_page")
    @patch("builtins.open")
    @patch("scrapers.providers.jacobs_scraper.json.load")
    def test_http_202_is_classified_as_upstream_access_challenge(
        self, load, _open, fetch_search_page
    ):
        load.return_value = {"country_id": 76515, "records_per_page": 100}
        fetch_search_page.return_value = Mock(status_code=202)

        with self.assertRaises(JacobsSourceUnavailable) as raised:
            JacobsScraper("jacobs").run()

        self.assertEqual("upstream_access_challenge", raised.exception.classification)
        self.assertIn("HTTP 202", str(raised.exception))
        fetch_search_page.assert_called_once()


if __name__ == "__main__":
    unittest.main()
