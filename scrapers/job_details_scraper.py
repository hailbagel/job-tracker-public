import sys
import os
import importlib

from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    tqdm_module = importlib.import_module("tqdm")
    tqdm = tqdm_module.tqdm
except Exception:
    class tqdm:
        def __init__(self, iterable, **kwargs):
            self._iterable = iterable

        def __iter__(self):
            return iter(self._iterable)

        def __len__(self):
            return len(self._iterable)

        @staticmethod
        def write(msg):
            print(msg)

# ROOT PATH FIX
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if len(sys.argv) > 1:
    company = sys.argv[1]
else:
    company = "default"

print(f"\nFirma: {company}")
print(__file__)

import pandas as pd
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By

# ========================================
# TEST LIMIT
# ========================================

TEST_LIMIT = 0

# ========================================
# CHECKPOINT SETTINGS
# ========================================

CHECKPOINT_INTERVAL = 25

# ========================================
# PATHS
# ========================================

base_data_path = f"data/{company}"
processed_path = os.path.join(base_data_path, "processed")

jobs_file = os.path.join(processed_path, "jobs_latest.csv")
details_file = os.path.join(processed_path, "job_details.csv")

# ========================================
# READ JOBS (SAFE)
# ========================================

try:
    jobs_df = pd.read_csv(jobs_file)

    jobs_df = jobs_df.drop_duplicates(
    subset=["link"]
)

    if jobs_df.empty:
        print("\nKeine Jobs in jobs_latest.csv - Detail Scraper wird uebersprungen")
        sys.exit(0)

except FileNotFoundError:
    print("\njobs_latest.csv fehlt - nichts zu tun")
    sys.exit(0)

except pd.errors.EmptyDataError:
    print("\njobs_latest.csv ist leer - nichts zu tun")
    sys.exit(0)

# ========================================
# LOAD EXISTING DETAILS
# ========================================

if os.path.exists(details_file):

    existing_df = pd.read_csv(details_file)
    existing_links = set(existing_df["link"])

    print(f"\n[OK] Bereits gespeicherte Jobs: {len(existing_df)}")

else:

    existing_df = pd.DataFrame()
    existing_links = set()

    print("\n[OK] Keine bestehende job_details.csv gefunden")

# ========================================
# FILTER NEW JOBS
# ========================================

jobs_to_process = jobs_df[
    ~jobs_df["link"].isin(existing_links)
].copy()

print("\n========================================")
print("DETAIL SCRAPER")
print("========================================")

print(
    f"Bereits gespeichert: {len(existing_df)}"
)

print(
    f"Aktuelle Jobs: {len(jobs_df)}"
)

print(
    f"Neue Jobs zu verarbeiten: {len(jobs_to_process)}"
)

if len(jobs_to_process) == 0:

    print("\nKeine neuen Jobs gefunden.")
    print("Detail Scraper wird uebersprungen.")

    sys.exit(0)

# ========================================
# DYNAMIC PARSER LOAD
# ========================================

parse_function = None

try:

    module_name = f"scrapers.providers.{company}_details"
    function_name = f"parse_{company}_details"

    module = __import__(module_name, fromlist=[function_name])
    parse_function = getattr(module, function_name)

    print(f"[OK] Verwende Parser: {function_name}")

except Exception as e:

    print(
        f"[WARN] Kein spezifischer Parser fuer {company} gefunden:",
        e
    )

# ========================================
# BROWSER
# ========================================

driver = webdriver.Edge()

new_rows = []

saved_checkpoints = 0
processed_new_jobs = 0
aborted_by_user = False

# ========================================
# CHECKPOINT HELPER
# ========================================

def save_checkpoint():

    global new_rows
    global saved_checkpoints

    if not new_rows:
        return

    checkpoint_df = pd.DataFrame(new_rows)

    if os.path.exists(details_file):

        try:

            existing_checkpoint_df = pd.read_csv(details_file)

            checkpoint_df = pd.concat(
                [
                    existing_checkpoint_df,
                    checkpoint_df
                ],
                ignore_index=True
            )

            checkpoint_df = checkpoint_df.drop_duplicates(
                subset=["link"],
                keep="last"
            )

        except Exception as e:

            print(
                "[WARN] Konnte bestehende Datei nicht laden:",
                e
            )

    checkpoint_df.to_csv(
        details_file,
        index=False
    )

    existing_links.update(
        row["link"]
        for row in new_rows
    )

    saved_checkpoints += 1

    print("\n----------------------------------------")
    print(f"[OK] Checkpoint #{saved_checkpoints}")
    print("----------------------------------------")
    print(f"Jobs aktuell gespeichert: {len(checkpoint_df)}")
    print(f"Datei: {details_file}")
    print("----------------------------------------")

    new_rows = []

# ========================================
# LOOP
# ========================================

try:

    for idx, (_, job) in enumerate(

        tqdm(
            jobs_to_process.iterrows(),
            total=len(jobs_to_process),
            desc=f"{company.upper()} Details",
            unit="job"
        ),

        start=1

    ):

        if TEST_LIMIT and idx > TEST_LIMIT:
            print("\nTest Limit Details erreicht")
            break

        try:

            tqdm.write(
                f"[{idx}/{len(jobs_to_process)}] "
                f"{job['title']}"
            )

            driver.get(job["link"])
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )   

            mission = ""
            requirements = ""
            benefits = ""

            # ========================================
            # MODULAR PARSER
            # ========================================

            if parse_function:

                try:

                    mission, requirements, benefits = (
                        parse_function(driver)
                    )

                except Exception as e:

                    print(
                        "Fehler im Parser:",
                        e
                    )

            # ========================================
            # FALLBACK
            # ========================================

            if not mission and not requirements:

                try:

                    body = driver.find_element(
                        By.TAG_NAME,
                        "body"
                    )

                    text = body.text

                    mission = text[:1000]
                    requirements = text[:1000]

                except:
                    pass

            # ========================================
            # SAVE ROW
            # ========================================

            new_rows.append({
                "title": job["title"],
                "location": job["location"],
                "company": job["company"],
                "department": job["department"],
                "link": job["link"],
                "mission": mission,
                "requirements": requirements,
                "benefits": benefits,
                "scrape_timestamp": datetime.now().strftime(
                    "%Y-%m-%d_%H-%M-%S"
                )
            })

            processed_new_jobs += 1

            # ========================================
            # CHECKPOINT
            # ========================================

            if len(new_rows) >= CHECKPOINT_INTERVAL:

                save_checkpoint()

        except Exception as e:

            print(
                f"\n[FEHLER] {job['title']}"
            )
            print(e)

except KeyboardInterrupt:

    aborted_by_user = True

    print("\n")
    print("========================================")
    print("[WARN] SCRAPER DURCH BENUTZER ABGEBROCHEN")
    print("========================================")

    print("\nSpeichere letzte nicht gesicherte Jobs...")

    save_checkpoint()

finally:

    driver.quit()

# ========================================
# FINAL SAVE
# ========================================

save_checkpoint()

# ========================================
# SUMMARY
# ========================================

print("\n========================================")

if aborted_by_user:
    print("DETAIL SCRAPER ABBRUCH SUMMARY")
else:
    print("DETAIL SCRAPER SUMMARY")

print("========================================")

print(f"Neue Jobs verarbeitet: {processed_new_jobs}")
print(f"Checkpoints gespeichert: {saved_checkpoints}")
print(f"Datei: {details_file}")

if os.path.exists(details_file):

    try:

        final_count = len(
            pd.read_csv(details_file)
        )

        print(
            f"Jobs aktuell gespeichert: {final_count}"
        )

    except Exception as e:

        print(
            "[WARN] Konnte Anzahl nicht bestimmen:",
            e
        )

print("\nDetail Scraper fertig")