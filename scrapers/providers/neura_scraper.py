import os
import time
from datetime import datetime

import pandas as pd
import requests

from scrapers.base.base_scraper import BaseScraper


API_BASE = "https://api.my-job-shop.com"
TENANT_ID = "neura-robotics"
JOB_SHOP_ID = "013afa23-9bcb-476e-ad6f-9965eacc5874"
JOB_SHOP_VANITY = "career"
OFFERS_PER_PAGE = 250


class NeuraSourceUnavailable(RuntimeError):
    def __init__(self, classification, detail):
        self.classification = classification
        super().__init__(f"NEURA source unavailable [{classification}]: {detail}")


def _json(response, operation):
    if response.status_code != 200:
        raise NeuraSourceUnavailable(
            "upstream_http_error",
            f"{operation} returned HTTP {response.status_code}",
        )
    try:
        return response.json()
    except ValueError as exc:
        raise NeuraSourceUnavailable(
            "upstream_invalid_response", f"{operation} returned invalid JSON"
        ) from exc


def _get_search_key(session, timeout=20):
    response = session.get(
        f"{API_BASE}/api/offer/v1/search/api-key",
        headers={"Accept": "application/json", "X-Tenant-Id": TENANT_ID},
        params={"filter": f"backoffice_vanity:{JOB_SHOP_VANITY}"},
        timeout=timeout,
    )
    key = _json(response, "public search-key endpoint").get("key")
    if not key:
        raise NeuraSourceUnavailable(
            "upstream_invalid_response", "public search-key endpoint omitted its key"
        )
    return key


def _fetch_offers_page(session, search_key, page, timeout=20):
    response = session.post(
        f"{API_BASE}/api/typesense/multi_search",
        headers={
            "Content-Type": "application/json",
            "X-Tenant-Id": TENANT_ID,
            "X-JobShop-Id": JOB_SHOP_ID,
            "X-Typesense-Api-Key": search_key,
        },
        json={
            "searches": [{
                "collection": "offers",
                "q": "*",
                "include_fields": (
                    "offer_uuid,title,location,company,department,url,"
                    "full_address,external_id"
                ),
                "sort_by": "create_date_timestamp:desc",
                "per_page": OFFERS_PER_PAGE,
                "page": page,
            }]
        },
        timeout=timeout,
    )
    payload = _json(response, f"public job search page {page}")
    try:
        return payload["results"][0]
    except (KeyError, IndexError, TypeError) as exc:
        raise NeuraSourceUnavailable(
            "upstream_invalid_response", f"public job search page {page} omitted results"
        ) from exc


def _first(value, default="Unknown"):
    if isinstance(value, list):
        value = value[0] if value else ""
    return str(value or default).strip() or default


def collect_jobs(session=None, timestamp=None):
    session = session or requests.Session()
    timestamp = timestamp or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    search_key = _get_search_key(session)
    jobs = []
    seen = set()
    page = 1
    found = None

    while found is None or len(seen) < found:
        result = _fetch_offers_page(session, search_key, page)
        try:
            found = int(result["found"])
            hits = result["hits"]
        except (KeyError, TypeError, ValueError) as exc:
            raise NeuraSourceUnavailable(
                "upstream_invalid_response", f"public job search page {page} was malformed"
            ) from exc
        if not hits:
            break
        for hit in hits:
            document = hit.get("document", {})
            link = str(document.get("url") or "").strip()
            title = str(document.get("title") or "").strip()
            native_id = document.get("offer_uuid") or document.get("external_id")
            identity = str(native_id or link).strip()
            if not identity or not link or not title or identity in seen:
                continue
            seen.add(identity)
            jobs.append({
                "title": title,
                "location": _first(document.get("location")),
                "company": str(document.get("company") or "NEURA Robotics").strip(),
                "department": _first(document.get("department")),
                "link": link,
                "scrape_timestamp": timestamp,
            })
        page += 1

    if found is None or len(seen) != found:
        raise NeuraSourceUnavailable(
            "upstream_incomplete_response",
            f"public job search returned {len(seen)} of {found or 0} jobs",
        )
    return jobs


class NeuraScraper(BaseScraper):
    def run(self):
        start_time = time.time()
        raw_path = "data/neura/raw"
        processed_path = "data/neura/processed"
        os.makedirs(raw_path, exist_ok=True)
        os.makedirs(processed_path, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        jobs = collect_jobs(timestamp=timestamp)
        frame = pd.DataFrame(jobs).sort_values(
            by=["department", "location", "title"]
        ).drop_duplicates(subset=["link"])
        raw_file = os.path.join(raw_path, f"neura_jobs_raw_{timestamp}.csv")
        latest_file = os.path.join(processed_path, "jobs_latest.csv")
        frame.to_csv(raw_file, index=False)
        frame.to_csv(latest_file, index=False)

        print("\nSCRAPING ERFOLGREICH")
        print(f"Firma: NEURA Robotics\nJobs gesamt: {len(frame)}")
        print(f"Laufzeit: {round(time.time() - start_time, 1)} Sekunden")
        print(f"Raw Datei:\n{raw_file}\nLatest Datei:\n{latest_file}")
