import sys
import os

# ✅ FIX: root path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ========================================
# IMPORTS (nur aktive Scraper!)
# ========================================

from scrapers.providers.neura_scraper import NeuraScraper
from scrapers.providers.tesla_scraper import TeslaScraper
from scrapers.providers.jacobs_scraper import JacobsScraper

# ========================================
# SCRAPER MAP
# ========================================

SCRAPER_MAP = {
    "neura": NeuraScraper,
    "tesla": TeslaScraper,
    "jacobs": JacobsScraper
}

# ========================================
# MAIN
# ========================================

if __name__ == "__main__":

    if len(sys.argv) < 2:
        raise ValueError("Bitte Firma angeben!")

    company = sys.argv[1].lower()

    if company not in SCRAPER_MAP:
        raise ValueError(f"Kein Scraper fuer {company}")

    scraper_class = SCRAPER_MAP[company]

    scraper = scraper_class(company)
    scraper.run()
