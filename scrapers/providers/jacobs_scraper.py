from selenium import webdriver
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import importlib
import pandas as pd
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
            self._iterable = iterable

        def __iter__(self):
            return iter(self._iterable)

        @staticmethod
        def write(msg):
            print(msg)


class JacobsScraper:

    def __init__(self, company):

        self.company = company

    def run(self):

        with open(
            "configs/jacobs.json",
            "r",
            encoding="utf-8"
        ) as f:

            config = json.load(f)

        country = config["country"]
        country_id = config["country_id"]
        records_per_page = config["records_per_page"]

        start_time = time.time()

        print("\n========================================")
        print("JACOBS SCRAPER")
        print("========================================")
        print(f"Land: {country}")
        print(f"Records/Page: {records_per_page}")

        driver = webdriver.Edge()

        try:

            jobs = []

            offset = 0

            while True:

                url = (
                    "https://careers.jacobs.com/en_US/careers/SearchJobs/"
                    f"?4182=%5B{country_id}%5D"
                    "&4182_format=4422"
                    "&listFilterMode=1"
                    f"&jobRecordsPerPage={records_per_page}"
                    f"&jobOffset={offset}"
                )

                driver.get(url)

                time.sleep(5)

                job_links = driver.find_elements(
                    By.XPATH,
                    "//a[contains(@href,'/JobDetail/')]"
                )

                if len(job_links) == 0:

                    print("\nKeine weiteren Jobs gefunden.")
                    break

                jobs_before = len(jobs)

                for job in job_links:

                    try:

                        link = job.get_attribute(
                            "href"
                        )

                        parent = job.find_element(
                            By.XPATH,
                            "./ancestor::*[self::li or self::div][1]"
                        )

                        parent_text = parent.text

                        parts = [
                            p.strip()
                            for p in parent_text.split("|")
                        ]

                        header = parts[0]

                        lines = [
                            l.strip()
                            for l in header.split("\n")
                            if l.strip()
                        ]

                        if len(lines) < 2:
                            continue

                        title = lines[0]
                        location = lines[1]

                        department = ""

                        if len(parts) >= 4:
                            department = parts[3]

                        jobs.append({
                            "title": title,
                            "location": location,
                            "company": "Jacobs",
                            "department": department,
                            "link": link
                        })

                    except Exception as e:

                        print(
                            f"Fehler beim Job: {e}"
                        )

                page_jobs = len(jobs) - jobs_before

                page_number = (
                    offset // records_per_page
                ) + 1

                tqdm.write(
                    f"JACOBS Overview | "
                    f"Seite {page_number} | "
                    f"+{page_jobs} Jobs | "
                    f"Gesamt: {len(jobs)}"
                )

                if page_jobs == 0:
                    break

                offset += records_per_page

            jobs_df = pd.DataFrame(jobs)

            jobs_df = jobs_df.drop_duplicates(
                subset=["link"]
            )

            raw_path = "data/jacobs/raw"
            processed_path = "data/jacobs/processed"

            os.makedirs(
                raw_path,
                exist_ok=True
            )

            os.makedirs(
                processed_path,
                exist_ok=True
            )

            timestamp = datetime.now().strftime(
                "%Y-%m-%d_%H-%M-%S"
            )

            raw_file = os.path.join(
                raw_path,
                f"jacobs_jobs_raw_{timestamp}.csv"
            )

            latest_file = os.path.join(
                processed_path,
                "jobs_latest.csv"
            )

            jobs_df.to_csv(
                raw_file,
                index=False
            )

            jobs_df.to_csv(
                latest_file,
                index=False
            )

            runtime = round(
                time.time() - start_time,
                1
            )

            print("\n========================================")
            print("SCRAPING ERFOLGREICH")
            print("========================================")
            print("Firma: Jacobs")
            print(f"Land: {country}")
            print(f"Jobs gesamt: {len(jobs_df)}")
            print(f"Laufzeit: {runtime} Sekunden")

            print("\nRaw Datei:")
            print(raw_file)

            print("\nLatest Datei:")
            print(latest_file)

        finally:

            driver.quit()