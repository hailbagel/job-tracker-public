import os
import sys
from datetime import datetime

import certifi
import pandas as pd
import requests

from scrapers.base.base_scraper import BaseScraper


API_URL = "https://boards-api.greenhouse.io/v1/boards/spacex/jobs?content=true"


def _fetch_jobs(url, timeout=60):
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    }

    try:
        return requests.get(
            url,
            headers=headers,
            verify=certifi.where(),
            timeout=timeout,
        )
    except requests.exceptions.SSLError:
        return requests.get(
            url,
            headers=headers,
            verify=False,
            timeout=timeout,
        )


def _metadata_value(job, name):
    for item in job.get("metadata") or []:
        if str(item.get("name", "")).strip().lower() == name.lower():
            value = item.get("value")
            if isinstance(value, list):
                return ", ".join(str(part) for part in value)
            return str(value).strip() if value is not None else ""
    return ""


class SpaceXScraper(BaseScraper):

    def run(self):
        base_data_path = f"data/{self.company}"
        raw_path = os.path.join(base_data_path, "raw")
        processed_path = os.path.join(base_data_path, "processed")

        os.makedirs(raw_path, exist_ok=True)
        os.makedirs(processed_path, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        raw_file = os.path.join(raw_path, f"spacex_jobs_raw_{timestamp}.csv")
        latest_file = os.path.join(processed_path, "jobs_latest.csv")

        print("\n========================================")
        print("SPACEX SCRAPER")
        print("========================================")
        print("Lade Greenhouse Jobs API...")

        response = _fetch_jobs(API_URL)

        if response.status_code != 200:
            print(f"FEHLER: Greenhouse API antwortet mit Status {response.status_code}")
            print(response.text[:500])
            sys.exit(1)

        try:
            payload = response.json()
        except ValueError:
            print("FEHLER: Greenhouse API lieferte kein JSON")
            sys.exit(1)

        listings = payload.get("jobs") or []
        if not listings:
            print("FEHLER: Keine SpaceX Listings gefunden")
            sys.exit(1)

        jobs = []
        seen_links = set()

        for listing in listings:
            job_id = listing.get("id")
            title = str(listing.get("title") or "").strip()
            location_data = listing.get("location") or {}
            location = str(location_data.get("name") or "Unknown").strip()
            department = _metadata_value(listing, "Discipline") or "Unknown"
            link = str(listing.get("absolute_url") or "").strip()

            if not job_id or not title or not link or link in seen_links:
                continue

            seen_links.add(link)
            jobs.append({
                "id": job_id,
                "title": title,
                "location": location,
                "company": "SpaceX",
                "department": department,
                "link": link,
                "requisition_id": listing.get("requisition_id", ""),
                "first_published": listing.get("first_published", ""),
                "updated_at": listing.get("updated_at", ""),
                "scrape_timestamp": timestamp,
            })

        jobs_df = pd.DataFrame(jobs)
        if jobs_df.empty:
            print("FEHLER: Keine validen SpaceX Jobs erstellt")
            sys.exit(1)

        jobs_df.to_csv(raw_file, index=False)
        jobs_df.to_csv(latest_file, index=False)

        print("\nSCRAPING ERFOLGREICH")
        print(f"Jobs gesamt: {len(jobs_df)}")
        print("Raw Datei:")
        print(raw_file)
        print("Latest Datei:")
        print(latest_file)