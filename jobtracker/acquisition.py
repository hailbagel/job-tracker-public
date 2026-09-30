from __future__ import annotations

import hashlib
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser


USER_AGENT = "VuTruLabs-public-job-tracker/1.0"


@dataclass
class AcquisitionResult:
    jobs: list
    status: str = "success"
    coverage_complete: bool = True
    reason: str | None = None


def _get(url, timeout=30):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _clean(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _job(source, native_id, title, location, url, department="Unknown", **extra):
    native_id = _clean(native_id) or hashlib.sha256(url.encode()).hexdigest()[:16]
    return {
        "id": f"{source['id']}:{native_id}",
        "source_id": source["id"],
        "source_job_id": native_id,
        "title": _clean(title),
        "location": _clean(location) or "Unknown",
        "company": source["company"],
        "department": _clean(department) or "Unknown",
        "link": url,
        "mission": _clean(extra.get("mission")),
        "requirements": _clean(extra.get("requirements")),
        "benefits": _clean(extra.get("benefits")),
    }


def greenhouse(source, fetch=_get):
    payload = json.loads(fetch(source["adapter_config"]["url"]))
    jobs = []
    for item in payload.get("jobs", []):
        departments = item.get("departments") or []
        location = (item.get("location") or {}).get("name")
        jobs.append(_job(
            source, item.get("id"), item.get("title"), location, item.get("absolute_url"),
            departments[0].get("name") if departments else "Unknown",
            mission=item.get("content"),
        ))
    return AcquisitionResult([job for job in jobs if job["title"] and job["link"]])


def personio_xml(source, fetch=_get):
    root = ET.fromstring(fetch(source["adapter_config"]["url"]))
    jobs = []
    for item in root.findall(".//position"):
        native_id = item.findtext("id")
        url = item.findtext("url") or f"{source['careers_url'].rstrip('/')}/job/{native_id}"
        jobs.append(_job(
            source, native_id, item.findtext("name"), item.findtext("office"), url,
            item.findtext("department") or "Unknown",
            mission=" ".join(_clean(node.text) for node in item.findall(".//jobDescriptions/jobDescription/value")),
        ))
    return AcquisitionResult([job for job in jobs if job["title"] and job["link"]])


class _JobLinkParser(HTMLParser):
    def __init__(self, pattern):
        super().__init__()
        self.pattern = re.compile(pattern)
        self.current = None
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if self.pattern.search(href):
                self.current, self.text = href, []

    def handle_data(self, data):
        if self.current:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.current:
            self.links.append((self.current, _clean(" ".join(self.text))))
            self.current, self.text = None, []


def html_job_links(source, fetch=_get):
    config = source["adapter_config"]
    parser = _JobLinkParser(config["job_url_pattern"])
    parser.feed(fetch(config["url"]).decode("utf-8", "replace"))
    jobs, seen = [], set()
    for url, title in parser.links:
        if url in seen or not title:
            continue
        seen.add(url)
        native_id = re.search(config.get("id_pattern", r"/job/(\d+)"), url)
        jobs.append(_job(source, native_id.group(1) if native_id else None, title, "Unknown", url))
    return AcquisitionResult(jobs)


ADAPTERS = {
    "greenhouse": greenhouse,
    "personio_xml": personio_xml,
    "html_job_links": html_job_links,
}


def acquire(source, fetch=_get):
    if not source.get("enabled"):
        return AcquisitionResult([], "disabled", False, "source disabled")
    if source["acquisition_mode"] == "manual_discovery":
        return AcquisitionResult([], "manual_discovery", False, source["manual_reason"])
    adapter = ADAPTERS.get(source.get("adapter"))
    if adapter is None:
        return AcquisitionResult([], "failed", False, f"unknown adapter: {source.get('adapter')}")
    try:
        result = adapter(source, fetch=fetch)
        if not result.jobs:
            return AcquisitionResult([], "incomplete", False, "adapter returned zero jobs")
        return result
    except Exception as exc:
        return AcquisitionResult([], "failed", False, f"{type(exc).__name__}: {exc}")


def acquisition_metadata(source, result, observed_at=None):
    observed_at = observed_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    canonical = json.dumps(result.jobs, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return {
        "source_id": source["id"], "company": source["company"],
        "acquisition_mode": source["acquisition_mode"], "adapter": source.get("adapter"),
        "status": result.status, "reason": result.reason, "observed_at": observed_at,
        "records_written": len(result.jobs) if result.coverage_complete else 0,
        "coverage_complete": result.coverage_complete,
        "data_hash": hashlib.sha256(canonical.encode()).hexdigest() if result.jobs else None,
    }
