import json
import os
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests

from scrapers.base.base_scraper import BaseScraper


API_BASE = "https://api.my-job-shop.com"
TENANT_ID = "neura-robotics"
JOB_SHOP_ID = "013afa23-9bcb-476e-ad6f-9965eacc5874"
JOB_SHOP_VANITY = "career"
OFFERS_PER_PAGE = 250
API_FIELDS = (
    "offer_uuid,title,location,location_objects,company,department,url,"
    "full_address,external_id,description,expectation,benefits,offering,"
    "about,introduction,additional,work_mode,salary,application_url,"
    "company_url,pitch_you_url"
)
LATEST_FIELDS = (
    "title", "location", "company", "department", "link", "scrape_timestamp",
    "locations", "departments", "location_objects", "full_address", "work_mode",
    "salary", "application_url", "company_url", "pitch_you_url", "offer_uuid",
    "external_id",
)
DETAIL_FIELDS = LATEST_FIELDS + (
    "mission", "requirements", "benefits", "description", "expectation",
    "offering", "about", "introduction", "additional", "full_text",
)


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
                "include_fields": API_FIELDS,
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


def _text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(str(item).strip() for item in value if str(item).strip())
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _structured(value):
    if value in (None, "", []):
        return ""
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _normalise_document(document, timestamp):
    if not isinstance(document, dict):
        raise NeuraSourceUnavailable(
            "upstream_invalid_response", "public job search returned a malformed document"
        )
    link = str(document.get("url") or "").strip()
    title = str(document.get("title") or "").strip()
    native_id = document.get("offer_uuid") or document.get("external_id")
    identity = str(native_id or link).strip()
    if not identity or not link or not title:
        raise NeuraSourceUnavailable(
            "upstream_invalid_response", "public job search returned an incomplete document"
        )
    rich = {
        field: _text(document.get(field))
        for field in (
            "description", "expectation", "benefits", "offering", "about",
            "introduction", "additional",
        )
    }
    return identity, {
        "title": title,
        "location": _first(document.get("location")),
        "company": _first(document.get("company"), "NEURA Robotics"),
        "department": _first(document.get("department")),
        "link": link,
        "scrape_timestamp": timestamp,
        "locations": _structured(document.get("location")),
        "departments": _structured(document.get("department")),
        "location_objects": _structured(document.get("location_objects")),
        "full_address": _text(document.get("full_address")),
        "work_mode": _structured(document.get("work_mode")),
        "salary": _structured(document.get("salary")),
        "application_url": _text(document.get("application_url")),
        "company_url": _text(document.get("company_url")),
        "pitch_you_url": _text(document.get("pitch_you_url")),
        "offer_uuid": _text(document.get("offer_uuid")),
        "external_id": _text(document.get("external_id")),
        "mission": rich["description"],
        "requirements": rich["expectation"],
        **rich,
        "full_text": "\n\n".join(value for value in rich.values() if value),
    }

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
            if found <= 0 or not isinstance(hits, list):
                raise ValueError
        except (KeyError, TypeError, ValueError) as exc:
            raise NeuraSourceUnavailable(
                "upstream_invalid_response", f"public job search page {page} was malformed"
            ) from exc
        if not hits:
            break
        for hit in hits:
            if not isinstance(hit, dict) or "document" not in hit:
                raise NeuraSourceUnavailable(
                    "upstream_invalid_response",
                    f"public job search page {page} contained a malformed hit",
                )
            identity, job = _normalise_document(hit["document"], timestamp)
            if identity in seen:
                continue
            seen.add(identity)
            jobs.append(job)
        page += 1

    if found is None or len(seen) != found:
        raise NeuraSourceUnavailable(
            "upstream_incomplete_response",
            f"public job search returned {len(seen)} of {found or 0} jobs",
        )
    return jobs


def _write_csv(frame, path, fields):
    temporary = path.with_name(f".{path.name}.tmp")
    frame.loc[:, fields].to_csv(temporary, index=False)
    os.replace(temporary, path)


class NeuraScraper(BaseScraper):
    def run(self, data_root="data", session=None, timestamp=None):
        start_time = time.time()
        timestamp = timestamp or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        jobs = collect_jobs(session=session, timestamp=timestamp)
        frame = pd.DataFrame(jobs).sort_values(
            by=["department", "location", "title"]
        ).drop_duplicates(subset=["link"])

        source_root = Path(data_root) / "neura"
        raw_path = source_root / "raw"
        processed_path = source_root / "processed"
        raw_path.mkdir(parents=True, exist_ok=True)
        processed_path.mkdir(parents=True, exist_ok=True)
        raw_file = raw_path / f"neura_jobs_raw_{timestamp}.csv"
        latest_file = processed_path / "jobs_latest.csv"
        details_file = processed_path / "job_details.csv"
        _write_csv(frame, raw_file, DETAIL_FIELDS)
        _write_csv(frame, latest_file, LATEST_FIELDS)
        _write_csv(frame, details_file, DETAIL_FIELDS)

        print("\nSCRAPING ERFOLGREICH")
        print(f"Firma: NEURA Robotics\nJobs gesamt: {len(frame)}")
        print(f"Laufzeit: {round(time.time() - start_time, 1)} Sekunden")
        print(
            f"Raw Datei:\n{raw_file}\nLatest Datei:\n{latest_file}"
            f"\nDetails Datei:\n{details_file}"
        )
