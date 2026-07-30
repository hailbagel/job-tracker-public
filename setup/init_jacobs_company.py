import os
import json

print()
print("========================================")
print("JACOBS COMPANY INITIALIZER")
print("========================================")

# ========================================
# PATHS
# ========================================

company = "jacobs"

data_path = os.path.join(
    "data",
    company
)

raw_path = os.path.join(
    data_path,
    "raw"
)

processed_path = os.path.join(
    data_path,
    "processed"
)

exports_path = os.path.join(
    data_path,
    "exports"
)

provider_path = os.path.join(
    "scrapers",
    "providers"
)

scraper_file = os.path.join(
    provider_path,
    "jacobs_scraper.py"
)

details_file = os.path.join(
    provider_path,
    "jacobs_details.py"
)

config_file = os.path.join(
    "configs",
    "companies.json"
)

# ========================================
# CREATE FOLDERS
# ========================================

for path in [
    data_path,
    raw_path,
    processed_path,
    exports_path
]:
    os.makedirs(path, exist_ok=True)

    print(f"[OK] Ordner: {path}")

# ========================================
# CREATE SCRAPER
# ========================================

if not os.path.exists(scraper_file):

    with open(
        scraper_file,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
'''class JacobsScraper:

    def run(self):
        print("Jacobs Scraper laeuft")
'''
        )

    print(f"[OK] Datei erstellt: {scraper_file}")

else:

    print(f"[OK] Datei existiert bereits: {scraper_file}")

# ========================================
# CREATE DETAIL PARSER
# ========================================

if not os.path.exists(details_file):

    with open(
        details_file,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
'''def parse_jacobs_details(driver):

    mission = ""
    requirements = ""
    benefits = ""

    return (
        mission,
        requirements,
        benefits
    )
'''
        )

    print(f"[OK] Datei erstellt: {details_file}")

else:

    print(f"[OK] Datei existiert bereits: {details_file}")

# ========================================
# UPDATE CONFIG
# ========================================

try:

    companies = []

    if os.path.exists(config_file):

        with open(
            config_file,
            "r",
            encoding="utf-8"
        ) as f:

            companies = json.load(f)

    exists = any(
        c["name"] == "jacobs"
        for c in companies
    )

    if not exists:

        companies.append({
            "name": "jacobs",
            "enabled": False
        })

        with open(
            config_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                companies,
                f,
                indent=2
            )

        print(
            "[OK] Jacobs zu companies.json hinzugefuegt"
        )

    else:

        print(
            "[OK] Jacobs bereits in companies.json vorhanden"
        )

except Exception as e:

    print(
        "[WARN] companies.json konnte nicht aktualisiert werden:",
        e
    )

print()
print("========================================")
print("FERTIG")
print("========================================")