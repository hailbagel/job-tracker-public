import csv
import hashlib
import html
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser

import certifi
import pandas as pd
import requests

from scrapers.base.base_scraper import BaseScraper


API_URL = "https://boards-api.greenhouse.io/v1/boards/spacex/jobs?content=true"


class _TextExtractor(HTMLParser):
    BLOCKS = {"br", "p", "div", "li", "ul", "ol", "h1", "h2", "h3", "h4", "strong"}

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.BLOCKS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)


def _html_text(value):
    parser = _TextExtractor()
    parser.feed(html.unescape(str(value or "")))
    return "\n".join(line.strip() for line in "".join(parser.parts).splitlines() if line.strip())


def _content_sections(value):
    text = _html_text(value)
    index = text.upper().find("BASIC QUALIFICATIONS:")
    if index < 0:
        return text[:1200], text, ""
    return text[:index][:1200], text[index:], ""


def _fetch_jobs(url, timeout=60):
    headers = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    }
    try:
        return requests.get(url, headers=headers, verify=certifi.where(), timeout=timeout)
    except requests.exceptions.SSLError:
        return requests.get(url, headers=headers, verify=False, timeout=timeout)


def _metadata_value(job, name):
    for item in job.get("metadata") or []:
        if str(item.get("name", "")).strip().lower() == name.lower():
            value = item.get("value")
            if isinstance(value, list):
                return ", ".join(str(part) for part in value)
            return str(value).strip() if value is not None else ""
    return ""


def _atomic_frame(frame, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    handle = tempfile.NamedTemporaryFile(dir=os.path.dirname(path), prefix=".spacex.", suffix=".csv", delete=False)
    handle.close()
    try:
        frame.to_csv(handle.name, index=False)
        os.replace(handle.name, path)
    finally:
        if os.path.exists(handle.name):
            os.unlink(handle.name)


def _atomic_json(value, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    handle = tempfile.NamedTemporaryFile(dir=os.path.dirname(path), prefix=".spacex.", suffix=".json", mode="w", encoding="utf-8", delete=False)
    try:
        with handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, path)
    finally:
        if os.path.exists(handle.name):
            os.unlink(handle.name)


def _read_acquisition(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError):
        return {}


def _record_incomplete(path, previous, observed_at, reason, source_records=0, status="incomplete"):
    acquisition = {
        "provider": "spacex", "source": API_URL, "status": status, "reason": reason,
        "observed_at": observed_at, "data_changed_at": previous.get("data_changed_at"),
        "data_hash": previous.get("data_hash"), "source_records": source_records,
        "records_written": 0, "coverage_complete": False,
    }
    _atomic_json(acquisition, path)


def _csv_record_count(path):
    with open(path, newline="", encoding="utf-8") as handle:
        return sum(1 for _ in csv.DictReader(handle))


class SpaceXScraper(BaseScraper):

    def run(self):
        base_data_path = f"data/{self.company}"
        raw_path = os.path.join(base_data_path, "raw")
        processed_path = os.path.join(base_data_path, "processed")
        os.makedirs(raw_path, exist_ok=True)
        os.makedirs(processed_path, exist_ok=True)

        observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        raw_file = os.path.join(raw_path, f"spacex_jobs_raw_{timestamp}.csv")
        latest_file = os.path.join(processed_path, "jobs_latest.csv")
        details_file = os.path.join(processed_path, "job_details.csv")
        acquisition_file = os.path.join(processed_path, "acquisition.json")

        print("\n========================================")
        print("SPACEX SCRAPER")
        print("========================================")
        print("Lade Greenhouse Jobs API...")
        previous = _read_acquisition(acquisition_file)
        try:
            response = _fetch_jobs(API_URL)
        except Exception as exc:
            _record_incomplete(
                acquisition_file, previous, observed_at, f"{type(exc).__name__}: {exc}", status="failed",
            )
            raise
        if response.status_code != 200:
            _record_incomplete(
                acquisition_file, previous, observed_at,
                f"Greenhouse API returned HTTP {response.status_code}", status="failed",
            )
            print(f"FEHLER: Greenhouse API antwortet mit Status {response.status_code}")
            print(response.text[:500])
            sys.exit(1)
        try:
            payload = response.json()
        except ValueError:
            _record_incomplete(
                acquisition_file, previous, observed_at, "Greenhouse API returned invalid JSON", status="failed",
            )
            print("FEHLER: Greenhouse API lieferte kein JSON")
            sys.exit(1)

        listings = payload.get("jobs") or []
        if not listings:
            _record_incomplete(acquisition_file, previous, observed_at, "Greenhouse API returned zero jobs")
            print("FEHLER: Keine SpaceX Listings gefunden; bestehende Dateien bleiben erhalten")
            sys.exit(1)

        jobs, details, seen_links = [], [], set()
        try:
            for listing in listings:
                job_id = listing.get("id")
                title = str(listing.get("title") or "").strip()
                location = str((listing.get("location") or {}).get("name") or "Unknown").strip()
                department = _metadata_value(listing, "Discipline") or "Unknown"
                link = str(listing.get("absolute_url") or "").strip()
                if not job_id or not title or not link or link in seen_links:
                    continue
                seen_links.add(link)
                jobs.append({
                    "id": job_id, "title": title, "location": location, "company": "SpaceX",
                    "department": department, "link": link, "requisition_id": listing.get("requisition_id", ""),
                    "first_published": listing.get("first_published", ""), "updated_at": listing.get("updated_at", ""),
                    "scrape_timestamp": timestamp,
                })
                mission, requirements, benefits = _content_sections(listing.get("content"))
                details.append({
                    "title": title, "location": location, "company": "SpaceX", "department": department,
                    "link": link, "mission": mission, "requirements": requirements, "benefits": benefits,
                    "scrape_timestamp": timestamp,
                })
        except Exception as exc:
            _record_incomplete(
                acquisition_file, previous, observed_at,
                f"Normalization failed: {type(exc).__name__}: {exc}", len(listings), status="failed",
            )
            raise

        if len(jobs) != len(listings) or len(details) != len(listings):
            _record_incomplete(
                acquisition_file, previous, observed_at,
                f"Normalized {len(jobs)} of {len(listings)} source records", len(listings),
            )
            print(f"FEHLER: Unvollstaendige SpaceX Erfassung ({len(jobs)}/{len(listings)}); bestehende Dateien bleiben erhalten")
            sys.exit(1)

        semantic = {
            "jobs": [{key: value for key, value in row.items() if key != "scrape_timestamp"} for row in jobs],
            "details": [{key: value for key, value in row.items() if key != "scrape_timestamp"} for row in details],
        }
        data_hash = hashlib.sha256(json.dumps(semantic, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        data_changed_at = (
            previous.get("data_changed_at") or observed_at
            if previous.get("data_hash") == data_hash else observed_at
        )
        jobs_df, details_df = pd.DataFrame(jobs), pd.DataFrame(details)
        try:
            _atomic_frame(jobs_df, raw_file)
            _atomic_frame(jobs_df, latest_file)
            _atomic_frame(details_df, details_file)
            records_written = _csv_record_count(latest_file)
        except Exception as exc:
            _record_incomplete(
                acquisition_file, previous, observed_at,
                f"Dataset write failed: {type(exc).__name__}: {exc}", len(listings), status="failed",
            )
            raise
        acquisition = {
            "provider": "spacex", "source": API_URL, "status": "success", "reason": None,
            "observed_at": observed_at, "data_changed_at": data_changed_at, "data_hash": data_hash,
            "source_records": len(listings), "records_written": records_written,
            "coverage_complete": True,
        }
        _atomic_json(acquisition, acquisition_file)

        print("\nSCRAPING ERFOLGREICH")
        print(f"Jobs gesamt: {len(jobs_df)}")
        print(f"Raw Datei:\n{raw_file}")
        print(f"Latest Datei:\n{latest_file}")
        print(f"Details Datei:\n{details_file}")
        print("Coverage: complete")
