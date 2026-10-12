from __future__ import annotations

import hashlib
import html
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


class _HTMLTextParser(HTMLParser):
    BLOCK_TAGS = {"br", "div", "h1", "h2", "h3", "h4", "li", "ol", "p", "ul"}

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag.lower() in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        self.parts.append(data)


def _html_text(value):
    parser = _HTMLTextParser()
    parser.feed(html.unescape(str(value or "")))
    return "\n".join(
        " ".join(line.split())
        for line in "".join(parser.parts).splitlines()
        if line.strip()
    )


def _job(source, native_id, title, location, url, department="", **extra):
    native_id = _clean(native_id) or hashlib.sha256(url.encode()).hexdigest()[:16]
    return {
        "id": f"{source['id']}:{native_id}",
        "source_id": source["id"],
        "source_job_id": native_id,
        "title": _clean(title),
        "location": _clean(location),
        "company": _clean(extra.get("company")) or source["company"],
        "department": _clean(department),
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
            departments[0].get("name") if departments else "",
            mission=item.get("content"),
        ))
    return AcquisitionResult([job for job in jobs if job["title"] and job["link"]])


def personio_xml(source, fetch=_get):
    root = ET.fromstring(fetch(source["adapter_config"]["url"]))
    jobs = []
    seen_ids = set()
    positions = root.findall(".//position")
    for item in positions:
        native_id = item.findtext("id")
        title = _clean(item.findtext("name"))
        url = _clean(item.findtext("url"))
        if not url and native_id:
            url_template = source["adapter_config"].get("job_url_template")
            url = url_template.format(id=_clean(native_id)) if url_template else (
                f"{source['careers_url'].rstrip('/')}/job/{_clean(native_id)}"
            )
        if not _clean(native_id) or not title or not url or _clean(native_id) in seen_ids:
            return AcquisitionResult(
                jobs, "incomplete", False,
                "Personio XML contains a position without a unique id, title, or canonical URL",
            )
        seen_ids.add(_clean(native_id))
        descriptions = {"mission": [], "requirements": [], "benefits": []}
        for description in item.findall("./jobDescriptions/jobDescription"):
            name = _clean(description.findtext("name")).lower()
            value = _html_text(description.findtext("value"))
            if not value:
                continue
            if "benefit" in name or "perk" in name:
                section = "benefits"
            elif any(term in name for term in ("qualification", "requirement", "experience", "profile")):
                section = "requirements"
            elif "location" in name or "equal employment" in name:
                continue
            else:
                section = "mission"
            descriptions[section].append(value)

        jobs.append(_job(
            source, native_id, title, item.findtext("office"), url,
            item.findtext("department"),
            company=item.findtext("subcompany"),
            mission=" ".join(descriptions["mission"]),
            requirements=" ".join(descriptions["requirements"]),
            benefits=" ".join(descriptions["benefits"]),
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
