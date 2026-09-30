import importlib
import json
import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCRAPER_MAP = {
    "neura": ("scrapers.providers.neura_scraper", "NeuraScraper"),
    "tesla": ("scrapers.providers.tesla_scraper", "TeslaScraper"),
    "jacobs": ("scrapers.providers.jacobs_scraper", "JacobsScraper"),
    "spacex": ("scrapers.providers.spacex_scraper", "SpaceXScraper"),
}
FAILURE_PREFIX = "PROVIDER_FAILURE: "


def load_scraper(company):
    module_name, class_name = SCRAPER_MAP[company]
    return getattr(importlib.import_module(module_name), class_name)


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        raise ValueError("Bitte Firma angeben!")

    company = argv[0].lower()
    if company not in SCRAPER_MAP:
        raise ValueError(f"Kein Scraper fuer {company}")

    scraper = load_scraper(company)(company)
    try:
        scraper.run()
    except Exception as exc:
        print(FAILURE_PREFIX + json.dumps({
            "classification": getattr(exc, "classification", "provider_execution_failed"),
            "reason": str(exc),
        }, sort_keys=True))
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
