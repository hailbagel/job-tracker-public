import unittest
from unittest.mock import patch

from scrapers.browser import create_edge_driver


class EdgeDriverTest(unittest.TestCase):
    @patch("scrapers.browser.webdriver.Edge")
    def test_uses_headless_linux_compatible_options(self, edge):
        driver = create_edge_driver()

        self.assertIs(driver, edge.return_value)
        options = edge.call_args.kwargs["options"]
        self.assertEqual(
            options.arguments,
            [
                "--headless=new",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--window-size=1920,1080",
            ],
        )


if __name__ == "__main__":
    unittest.main()
