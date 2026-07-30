import os
import sys
from datetime import datetime

import certifi
import pandas as pd
import requests

from scrapers.base.base_scraper import BaseScraper


def _fetch_state_json(url, timeout=20):
    session = requests.Session()
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }

    try:
        return session.get(url, headers=headers, verify=certifi.where(), timeout=timeout)
    except requests.exceptions.SSLError:
        return session.get(url, headers=headers, verify=False, timeout=timeout)


class TeslaScraper(BaseScraper):

    def run(self):

        print("Tesla Scraper laeuft")

        base_data_path = f"data/{self.company}"
        raw_path = os.path.join(base_data_path, "raw")
        processed_path = os.path.join(base_data_path, "processed")

        os.makedirs(raw_path, exist_ok=True)
        os.makedirs(processed_path, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        raw_file = os.path.join(raw_path, f"tesla_jobs_raw_{timestamp}.csv")
        latest_file = os.path.join(processed_path, "jobs_latest.csv")

        url = "https://www.tesla.com/cua-api/apps/careers/state"

        print("\nLade Tesla State API...")
        response = _fetch_state_json(url)

        if response.status_code != 200:
            print(f"FEHLER: State API antwortet mit Status {response.status_code}")
            print(response.text[:500])
            sys.exit(1)

        try:
            state = response.json()
        except Exception:
            print("FEHLER: State API lieferte kein JSON")
            sys.exit(1)

        listings = state.get("listings") or []
        lookup = state.get("lookup", {})
        location_map = lookup.get("locations", {})
        department_map = lookup.get("departments", {})
        type_map = lookup.get("types", {})

        print(f"Jobs gefunden in State API: {len(listings)}")

        if not listings:
            print("FEHLER: Keine Listings gefunden")
            sys.exit(1)

        jobs = []
        seen_links = set()

        for listing in listings:
            job_id = listing.get("id")
            title = listing.get("t", "").strip()
            location_id = str(listing.get("l", ""))
            department_id = str(listing.get("dp", ""))
            function_id = str(listing.get("f", ""))
            type_id = str(listing.get("y", ""))
            site_pref = listing.get("sp")
            posted_until = listing.get("pu")

            location = location_map.get(location_id) or "Unknown"
            department = department_map.get(department_id) or "Unknown"
            job_type = type_map.get(type_id) or "Unknown"
            link = f"https://www.tesla.com/careers/search/job/{job_id}"

            if not job_id or not title:
                continue

            if link in seen_links:
                continue

            seen_links.add(link)

            jobs.append({
                "id": job_id,
                "title": title,
                "location_id": location_id,
                "location": location,
                "company": "Tesla",
                "department_id": department_id,
                "department": department,
                "function_id": function_id,
                "type_id": type_id,
                "type": job_type,
                "site_pref": site_pref,
                "posted_until": posted_until,
                "link": link,
                "scrape_timestamp": timestamp,
            })

        df = pd.DataFrame(jobs)

        if df.empty:
            print("FEHLER: Keine validen Jobs erstellt")
            sys.exit(1)

        df.to_csv(raw_file, index=False)
        df.to_csv(latest_file, index=False)

        print("\nSCRAPING ERFOLGREICH")
        print(f"Jobs gesamt: {len(df)}")
        print("Raw Datei:")
        print(raw_file)
        print("Latest Datei:")
        print(latest_file)
