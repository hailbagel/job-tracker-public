import subprocess
import importlib
import sys
import time
import os
import json

from datetime import datetime

try:
    tqdm_module = importlib.import_module("tqdm")
    tqdm = tqdm_module.tqdm

except Exception:

    class tqdm:

        def __init__(self, iterable=None, **kwargs):
            self.total = kwargs.get("total", 0)

        def update(self, n=1):
            pass

        def close(self):
            pass

# ========================================
# CONFIG LADEN
# ========================================

config_path = "configs/companies.json"

if not os.path.exists(config_path):

    raise FileNotFoundError(
        f"Config nicht gefunden: {config_path}"
    )

with open(config_path) as f:

    companies_config = json.load(f)

active_companies = [

    c["name"]

    for c in companies_config

    if c["enabled"]

]

# ========================================
# PIPELINE STEPS
# ========================================

steps = [

    {
        "name": "OVERVIEW SCRAPER",
        "script": "scrapers/runner.py"
    },

    {
        "name": "DETAIL SCRAPER",
        "script": "scrapers/job_details_scraper.py"
    },

    {
        "name": "ANALYSIS PIPELINE",
        "script": "analysis/analysis.py"
    },

    {
        "name": "TXT EXPORT",
        "script": "analysis/export_txt.py"
    }
]

# ========================================
# START
# ========================================

pipeline_start = time.time()

print("\n========================================")
print("JOB INTELLIGENCE PIPELINE")
print("========================================")

print("\nStartzeit:")
print(
    datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
)

# ========================================
# COMPANIES CHECK
# ========================================

if not active_companies:

    print(
        "\n⚠️ Keine aktive Firma konfiguriert!"
    )

    print(
        "Bitte companies.json prüfen.\n"
    )

    sys.exit(0)

print("\nAktive Firmen:")

for c in active_companies:

    print(f"- {c}")

# ========================================
# PIPELINE PRO FIRMA
# ========================================

overall_success = True

for company in active_companies:

    print("\n========================================")
    print(
        f"STARTE PIPELINE FÜR: "
        f"{company.upper()}"
    )
    print("========================================")

    company_success = True
    total_steps = len(steps)

    pipeline_bar = tqdm(
        total=total_steps,
        desc=f"{company.upper()} Pipeline",
        unit="step"
    )

    for current_step, step in enumerate(
        steps,
        start=1
    ):

        step_name = step["name"]
        script_path = step["script"]

        step_start = time.time()

        print("\n----------------------------------------")
        print(
            f"[{current_step}/{total_steps}] "
            f"{step_name}"
        )
        print("----------------------------------------")

        print("\nStarte Script:")
        print(script_path)

        if not os.path.exists(script_path):

            print(
                f"\n❌ Script nicht gefunden:"
            )

            print(script_path)

            company_success = False
            overall_success = False

            break

        try:

            result = subprocess.run(
                [
                    sys.executable,
                    script_path,
                    company
                ]
            )

            if result.returncode != 0:

                print(
                    f"\n❌ SCHRITT FEHLGESCHLAGEN: "
                    f"{step_name}"
                )

                company_success = False
                overall_success = False

                break

            step_duration = round(
                time.time() - step_start,
                2
            )

            pipeline_bar.update(1)

            print("\n✅ SCHRITT ERFOLGREICH")
            print(
                f"Dauer: {step_duration} Sekunden"
            )

        except Exception as e:

            print("\n❌ PIPELINE FEHLER")
            print(e)

            company_success = False
            overall_success = False

            break

    pipeline_bar.close()

    # ========================================
    # STATUS PRO FIRMA
    # ========================================

    if company_success:

        print(
            f"\n✅ PIPELINE FÜR "
            f"{company.upper()} "
            f"ERFOLGREICH"
        )

    else:

        print(
            f"\n❌ PIPELINE FÜR "
            f"{company.upper()} "
            f"FEHLGESCHLAGEN"
        )

# ========================================
# ABSCHLUSS
# ========================================

pipeline_duration = round(
    time.time() - pipeline_start,
    2
)

print("\n========================================")
print("PIPELINE GESAMT ABGESCHLOSSEN")
print("========================================")

if overall_success:

    print("\n✅ STATUS: ERFOLGREICH")

else:

    print("\n❌ STATUS: TEILWEISE FEHLER")

print("\nGesamtdauer:")
print(f"{pipeline_duration} Sekunden")

print("\nEndzeit:")
print(
    datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
)

if not overall_success:

    sys.exit(1)
