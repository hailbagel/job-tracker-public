import json
import os
import time
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin

import pandas as pd
import requests

from scrapers.base.base_scraper import BaseScraper


class JacobsSourceUnavailable(RuntimeError):
    def __init__(self, classification, detail):
        self.classification = classification
        super().__init__(f"Jacobs source unavailable [{classification}]: {detail}")


def _fetch_search_page(url, timeout=20):
    return requests.get(
        url,
        headers={"Accept": "text/html", "User-Agent": "VuTruLabs-public-job-tracker/1.0"},
        timeout=timeout,
    )


class _JobLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.current = None
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if "/JobDetail/" in href:
                self.current = href
                self.text = []

    def handle_data(self, data):
        if self.current:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.current:
            self.links.append((self.current, " ".join(self.text).strip()))
            self.current = None
            self.text = []


def _parse_jobs(html, base_url):
    parser = _JobLinkParser()
    parser.feed(html)
    return [
        {
            "title": " ".join(title.split()),
            "location": "Unknown",
            "company": "Jacobs",
            "department": "Unknown",
            "link": urljoin(base_url, link),
        }
        for link, title in parser.links if title
    ]


class JacobsScraper(BaseScraper):
    def run(self):
        with open("configs/jacobs.json", encoding="utf-8") as handle:
            config = json.load(handle)

        start_time = time.time()
        records_per_page = config["records_per_page"]
        jobs = []
        seen = set()
        offset = 0

        while True:
            url = (
                "https://careers.jacobs.com/en_US/careers/SearchJobs/"
                f"?4182=%5B{config['country_id']}%5D&4182_format=4422"
                f"&listFilterMode=1&jobRecordsPerPage={records_per_page}"
                f"&jobOffset={offset}"
            )
            response = _fetch_search_page(url)
            if response.status_code == 202:
                raise JacobsSourceUnavailable(
                    "upstream_access_challenge",
                    "public careers search returned HTTP 202 access-control challenge",
                )
            if response.status_code in {401, 403}:
                raise JacobsSourceUnavailable(
                    "upstream_access_denied",
                    f"public careers search returned HTTP {response.status_code}",
                )
            if response.status_code != 200:
                raise JacobsSourceUnavailable(
                    "upstream_http_error",
                    f"public careers search returned HTTP {response.status_code}",
                )

            page_jobs = _parse_jobs(response.text, url)
            added = 0
            for job in page_jobs:
                if job["link"] not in seen:
                    seen.add(job["link"])
                    jobs.append(job)
                    added += 1
            if not page_jobs or added == 0 or len(page_jobs) < records_per_page:
                break
            offset += records_per_page

        if not jobs:
            raise JacobsSourceUnavailable(
                "upstream_invalid_response", "public careers search returned zero jobs"
            )

        frame = pd.DataFrame(jobs).drop_duplicates(subset=["link"])
        raw_path = "data/jacobs/raw"
        processed_path = "data/jacobs/processed"
        os.makedirs(raw_path, exist_ok=True)
        os.makedirs(processed_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        raw_file = os.path.join(raw_path, f"jacobs_jobs_raw_{timestamp}.csv")
        latest_file = os.path.join(processed_path, "jobs_latest.csv")
        frame.to_csv(raw_file, index=False)
        frame.to_csv(latest_file, index=False)

        print("\nSCRAPING ERFOLGREICH")
        print(f"Firma: Jacobs\nJobs gesamt: {len(frame)}")
        print(f"Laufzeit: {round(time.time() - start_time, 1)} Sekunden")
        print(f"Raw Datei:\n{raw_file}\nLatest Datei:\n{latest_file}")
