from scrapers.base.base_scraper import BaseScraper

from selenium import webdriver
from selenium.webdriver.common.by import By

import pandas as pd
import time
import os

from datetime import datetime


class NeuraScraper(BaseScraper):

    def run(self):

        start_time = time.time()

        print("\n========================================")
        print("NEURA SCRAPER")
        print("========================================")

        company = "neura"

        raw_path = f"data/{company}/raw"
        processed_path = f"data/{company}/processed"

        os.makedirs(raw_path, exist_ok=True)
        os.makedirs(processed_path, exist_ok=True)

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        raw_file = os.path.join(
            raw_path,
            f"neura_jobs_raw_{timestamp}.csv"
        )

        latest_file = os.path.join(
            processed_path,
            "jobs_latest.csv"
        )

        driver = webdriver.Edge()

        try:

            print("\nLade Neura Karriereportal...")

            driver.get(
                "https://jobs.neura-robotics.com/search"
            )

            time.sleep(5)

            try:

                buttons = driver.find_elements(
                    By.TAG_NAME,
                    "button"
                )

                for button in buttons:

                    text = (
                        button.text
                        .strip()
                        .lower()
                    )

                    if "accept" in text:

                        button.click()

                        print(
                            "Cookie Banner akzeptiert"
                        )

                        break

            except Exception:
                pass

            time.sleep(2)

            jobs = []
            seen_links = set()

            print("\nSammle Jobs...")

            last_count = 0
            scroll_round = 0

            while scroll_round < 20:

                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);"
                )

                time.sleep(2)

                print(
                    f"Scroll {scroll_round + 1}/20"
                )

                links = driver.find_elements(
                    By.TAG_NAME,
                    "a"
                )

                for link_element in links:

                    try:

                        href = link_element.get_attribute(
                            "href"
                        )

                        if not href:
                            continue

                        text = (
                            link_element.text
                            .strip()
                        )

                        if not text:
                            continue

                        lines = text.split("\n")

                        if len(lines) != 4:
                            continue

                        title = lines[0]

                        if "(human)" not in title.lower():
                            continue

                        if href in seen_links:
                            continue

                        seen_links.add(href)

                        jobs.append({
                            "title": lines[0],
                            "location": lines[1],
                            "company": lines[2],
                            "department": lines[3],
                            "link": href,
                            "scrape_timestamp": timestamp
                        })

                    except Exception:
                        continue

                current_count = len(seen_links)

                if current_count == last_count:
                    break

                last_count = current_count
                scroll_round += 1

            df = pd.DataFrame(jobs)

            if not df.empty:

                df = df.sort_values(
                    by=[
                        "department",
                        "location",
                        "title"
                    ]
                )

                df = df.drop_duplicates(
                    subset=["link"]
                )

            df.to_csv(
                raw_file,
                index=False
            )

            df.to_csv(
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

            print(
                f"Firma: Neura Robotics"
            )

            print(
                f"Jobs gesamt: {len(df)}"
            )

            print(
                f"Laufzeit: {runtime} Sekunden"
            )

            print("\nRaw Datei:")
            print(raw_file)

            print("\nLatest Datei:")
            print(latest_file)

        finally:

            driver.quit()