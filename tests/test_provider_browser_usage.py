import unittest
from unittest.mock import mock_open, patch

from scrapers.providers.jacobs_scraper import JacobsScraper
from scrapers.providers.neura_scraper import NeuraScraper


class ProviderBrowserUsageTest(unittest.TestCase):
    @patch("scrapers.providers.neura_scraper.create_edge_driver")
    @patch("scrapers.providers.neura_scraper.os.makedirs")
    @patch("scrapers.providers.neura_scraper.time.sleep")
    @patch("scrapers.providers.neura_scraper.pd.DataFrame.to_csv")
    def test_neura_uses_shared_edge_factory(
        self, _to_csv, _sleep, _makedirs, create_driver
    ):
        driver = create_driver.return_value
        driver.find_elements.return_value = []

        NeuraScraper("neura").run()

        create_driver.assert_called_once_with()
        driver.quit.assert_called_once_with()

    @patch("scrapers.providers.jacobs_scraper.create_edge_driver")
    @patch("builtins.open", new_callable=mock_open, read_data='{}')
    @patch("scrapers.providers.jacobs_scraper.json.load")
    @patch("scrapers.providers.jacobs_scraper.time.sleep")
    @patch("scrapers.providers.jacobs_scraper.pd.DataFrame.to_csv")
    def test_jacobs_uses_shared_edge_factory(
        self, _to_csv, _sleep, load, _open, create_driver
    ):
        load.return_value = {
            "country": "United States",
            "country_id": 76515,
            "records_per_page": 100,
        }
        driver = create_driver.return_value
        driver.find_elements.return_value = []

        JacobsScraper("jacobs").run()

        create_driver.assert_called_once_with()
        driver.quit.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
