from __future__ import annotations

import hashlib
import html
import json
import os
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlsplit


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


def _clean_multiline(value):
    return "\n".join(
        cleaned for line in str(value or "").splitlines()
        if (cleaned := _clean(line))
    )


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


_DESCRIPTION_HEADINGS = {
    "mission": {
        "about the role", "about the team", "job description", "responsibilities",
        "the role", "what you will do", "what you'll do", "your mission", "your tasks",
    },
    "requirements": {
        "basic qualifications", "minimum qualifications", "must-have skills",
        "must have skills", "qualifications", "required qualifications", "requirements",
        "what you bring", "what we're looking for", "your profile", "your qualifications",
    },
    "preferred": {
        "nice to have", "nice-to-have", "nice-to-have skills", "nice to have skills", "preferred qualifications",
        "preferred skills",
    },
    "benefits": {
        "benefits", "perks", "we offer", "what we offer", "why join us",
    },
}


def _description_heading(line):
    heading = re.sub(r"\s+", " ", str(line or "")).strip(" :.-").casefold()
    for section, headings in _DESCRIPTION_HEADINGS.items():
        if heading in headings:
            return section
    return None


def _structured_job_description(value):
    """Split common ATS description headings into the normalized detail contract."""
    descriptions = {"mission": [], "requirements": [], "benefits": []}
    section = "mission"
    requirement_kind = None
    for line in _html_text(value).splitlines():
        heading = _description_heading(line)
        if heading:
            if heading == "preferred":
                section, next_kind = "requirements", "preferred"
            elif heading == "requirements":
                section, next_kind = "requirements", "basic"
            else:
                section, next_kind = heading, None
            if section == "requirements" and next_kind != requirement_kind:
                descriptions[section].append(
                    "PREFERRED QUALIFICATIONS:" if next_kind == "preferred"
                    else "BASIC QUALIFICATIONS:"
                )
            requirement_kind = next_kind
            continue
        descriptions[section].append(line)
    return {
        key: "\n".join(part for part in parts if part).strip()
        for key, parts in descriptions.items()
    }


class _JSONLDParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.scripts = []
        self._script_type = None
        self._script_parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script":
            self._script_type = dict(attrs).get("type", "").lower()
            self._script_parts = []

    def handle_data(self, data):
        if self._script_type == "application/ld+json":
            self._script_parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self._script_type is not None:
            if self._script_type == "application/ld+json":
                self.scripts.append("".join(self._script_parts))
            self._script_type = None
            self._script_parts = []


class _DescriptionSectionsParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sections = []
        self._heading = ""
        self._heading_tag = None
        self._heading_parts = []
        self._parts = []

    def _finish_section(self):
        value = _clean(" ".join(self._parts))
        if self._heading or value:
            self.sections.append((self._heading, value))
        self._heading = ""
        self._parts = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in {"h1", "h2", "h3", "h4"}:
            self._finish_section()
            self._heading_tag = tag
            self._heading_parts = []
        elif tag in _HTMLTextParser.BLOCK_TAGS and self._heading_tag is None:
            self._parts.append(" ")

    def handle_data(self, data):
        if self._heading_tag is not None:
            self._heading_parts.append(data)
        else:
            self._parts.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == self._heading_tag:
            self._heading = _clean(" ".join(self._heading_parts))
            self._heading_tag = None
            self._heading_parts = []
        elif tag in _HTMLTextParser.BLOCK_TAGS and self._heading_tag is None:
            self._parts.append(" ")

    def close(self):
        super().close()
        self._finish_section()


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
        "requisition_id": _clean(extra.get("requisition_id")),
        "first_published": _clean(extra.get("first_published")),
        "updated_at": _clean(extra.get("updated_at")),
        "mission": _clean(extra.get("mission")),
        "requirements": _clean_multiline(extra.get("requirements")),
        "benefits": _clean(extra.get("benefits")),
    }


def _add_personio_description(descriptions, name, value, *, from_detail_page=False):
    name = _clean(name).lower()
    value = _clean(value)
    if not value:
        return
    if any(term in name for term in ("benefit", "perk", "why us", "warum wir")):
        section = "benefits"
    elif any(
        term in name
        for term in (
            "qualification", "qualifikation", "requirement", "anforderung",
            "experience", "profile", "profil",
        )
    ):
        section = "requirements"
    elif "location" in name or "equal employment" in name:
        return
    elif from_detail_page and any(
        term in name for term in ("how to apply", "application", "bewerb", "about us")
    ):
        return
    else:
        section = "mission"
    descriptions[section].append(value)


def _personio_page_descriptions(payload):
    document = _JSONLDParser()
    document.feed(
        payload.decode("utf-8", "replace") if isinstance(payload, bytes) else str(payload)
    )
    for script in document.scripts:
        structured = json.loads(script)
        entries = structured if isinstance(structured, list) else [structured]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            job_type = entry.get("@type", [])
            if not isinstance(job_type, list):
                job_type = [job_type]
            description = entry.get("description")
            if "JobPosting" not in job_type or not description:
                continue
            parser = _DescriptionSectionsParser()
            parser.feed(str(description))
            parser.close()
            descriptions = {"mission": [], "requirements": [], "benefits": []}
            for name, value in parser.sections:
                _add_personio_description(
                    descriptions, name, value, from_detail_page=True
                )
            return {
                key: " ".join(values)
                for key, values in descriptions.items()
            }
    return {"mission": "", "requirements": "", "benefits": ""}


def greenhouse(source, fetch=_get):
    payload = json.loads(fetch(source["adapter_config"]["url"]))
    jobs = []
    for item in payload.get("jobs", []):
        departments = item.get("departments") or []
        location = (item.get("location") or {}).get("name")
        descriptions = _structured_job_description(item.get("content"))
        jobs.append(_job(
            source, item.get("id"), item.get("title"), location, item.get("absolute_url"),
            departments[0].get("name") if departments else "",
            **descriptions,
            requisition_id=item.get("requisition_id"),
            first_published=item.get("first_published"),
            updated_at=item.get("updated_at"),
        ))
    return AcquisitionResult([job for job in jobs if job["title"] and job["link"]])


def personio_xml(source, fetch=_get):
    root = ET.fromstring(fetch(source["adapter_config"]["url"]))
    jobs = []
    detail_warnings = []
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
            name = description.findtext("name")
            value = _html_text(description.findtext("value"))
            _add_personio_description(descriptions, name, value)

        page_template = source["adapter_config"].get("job_detail_url_template")
        if page_template and not any(descriptions.values()):
            page_url = page_template.format(id=_clean(native_id))
            try:
                page = fetch(page_url)
            except (OSError, urllib.error.URLError) as exc:
                detail_warnings.append(
                    f"Personio detail page for job {native_id} unavailable "
                    f"({type(exc).__name__})"
                )
            else:
                try:
                    page_descriptions = _personio_page_descriptions(page)
                except json.JSONDecodeError:
                    detail_warnings.append(
                        f"Personio detail page for job {native_id} has invalid structured data"
                    )
                else:
                    for section, value in page_descriptions.items():
                        if value:
                            descriptions[section].append(value)
                    if not any(page_descriptions.values()):
                        detail_warnings.append(
                            f"Personio detail page for job {native_id} has no usable description"
                        )

        jobs.append(_job(
            source, native_id, title, item.findtext("office"), url,
            item.findtext("department"),
            company=item.findtext("subcompany"),
            mission=" ".join(descriptions["mission"]),
            requirements=" ".join(descriptions["requirements"]),
            benefits=" ".join(descriptions["benefits"]),
        ))
    return AcquisitionResult(
        [job for job in jobs if job["title"] and job["link"]],
        reason="; ".join(detail_warnings) if detail_warnings else None,
    )


def _dvinci_publication_id(url, host):
    parsed = urlsplit(_clean(url))
    if (
        parsed.scheme != "https"
        or parsed.hostname != host
        or parsed.port is not None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        return None
    match = re.fullmatch(
        r"/([a-z]{2}(?:[-_][a-z]{2})?)/jobs/(\d+)/[^/]+",
        parsed.path,
        re.IGNORECASE,
    )
    if not match:
        return None
    return match.group(1).lower().replace("_", "-"), match.group(2)


def _dvinci_display_name(value):
    if isinstance(value, dict):
        value = value.get("name")
    return _clean(value) if isinstance(value, str) else ""


def dvinci(source, fetch=_get):
    config = source["adapter_config"]
    host = urlsplit(source["careers_url"]).hostname
    feed_url = config["url"]
    sitemap_url = config["sitemap_url"]
    if (
        not host
        or urlsplit(feed_url).scheme != "https"
        or urlsplit(feed_url).hostname != host
        or urlsplit(sitemap_url).scheme != "https"
        or urlsplit(sitemap_url).hostname != host
    ):
        return AcquisitionResult(
            [], "incomplete", False,
            "d.vinci feed and sitemap must use the official careers host",
        )

    publications = json.loads(fetch(feed_url))
    if not isinstance(publications, list) or not publications:
        return AcquisitionResult(
            [], "incomplete", False,
            "d.vinci list endpoint returned no publication array",
        )

    publication_ids = set()
    publication_urls = set()
    openings = {}
    for item in publications:
        if not isinstance(item, dict):
            return AcquisitionResult(
                [], "incomplete", False,
                "d.vinci list contains a malformed publication",
            )
        publication_id = _clean(item.get("id"))
        opening = item.get("jobOpening")
        opening_id = _clean(opening.get("id")) if isinstance(opening, dict) else ""
        language = _clean(item.get("language")).lower().replace("_", "-")
        link = _clean(item.get("jobPublicationURL"))
        parsed_link = _dvinci_publication_id(link, host)
        if (
            not publication_id.isdigit()
            or not opening_id.isdigit()
            or not language
            or not parsed_link
            or parsed_link != (language, publication_id)
            or not isinstance(item.get("position") or item.get("pageTitle"), str)
            or not _clean(item.get("position") or item.get("pageTitle"))
        ):
            return AcquisitionResult(
                [], "incomplete", False,
                "d.vinci publication is missing a native ID, locale, title, or canonical URL",
            )
        if any(
            item.get(field) is not None and not isinstance(item.get(field), str)
            for field in ("introduction", "tasks", "profile", "weOffer")
        ):
            return AcquisitionResult(
                [], "incomplete", False,
                "d.vinci publication contains a malformed description field",
            )
        if publication_id in publication_ids or link in publication_urls:
            return AcquisitionResult(
                [], "incomplete", False,
                "d.vinci list contains a duplicate publication ID or URL",
            )
        publication_ids.add(publication_id)
        publication_urls.add(link)
        openings.setdefault(opening_id, []).append(item)

    sitemap_root = ET.fromstring(fetch(sitemap_url))
    if sitemap_root.tag.rsplit("}", 1)[-1] != "urlset":
        return AcquisitionResult(
            [], "incomplete", False,
            "d.vinci sitemap is not a URL set",
        )
    sitemap_ids = []
    for element in sitemap_root.iter():
        if element.tag.rsplit("}", 1)[-1] != "loc":
            continue
        parsed_link = _dvinci_publication_id(element.text or "", host)
        if not parsed_link:
            return AcquisitionResult(
                [], "incomplete", False,
                "d.vinci sitemap contains a non-canonical job URL",
            )
        sitemap_ids.append(parsed_link[1])
    if (
        not sitemap_ids
        or len(sitemap_ids) != len(set(sitemap_ids))
        or set(sitemap_ids) != publication_ids
    ):
        return AcquisitionResult(
            [], "incomplete", False,
            "d.vinci publication IDs do not match the public job sitemap "
            f"(feed={len(publication_ids)}, sitemap={len(sitemap_ids)})",
        )

    preferred_language = _clean(config.get("preferred_language") or "en").lower()
    jobs = []
    for opening_id, variants in openings.items():
        languages = [item["language"].lower().replace("_", "-") for item in variants]
        if len(languages) != len(set(languages)):
            return AcquisitionResult(
                [], "incomplete", False,
                f"d.vinci opening {opening_id} has duplicate publications in one locale",
            )
        selected = min(
            variants,
            key=lambda item: (
                item["language"].lower().replace("_", "-") != preferred_language,
                item["language"].lower().replace("_", "-"),
                str(item["id"]),
            ),
        )
        job_opening = selected["jobOpening"]
        location = _dvinci_display_name(job_opening.get("location"))
        if not location:
            location = _dvinci_display_name(job_opening.get("locations"))
        mission = " ".join(
            text for text in (
                _html_text(selected.get("introduction")),
                _html_text(selected.get("tasks")),
            ) if text
        )
        descriptions = {
            "mission": mission,
            "requirements": _html_text(selected.get("profile")),
            "benefits": _html_text(selected.get("weOffer")),
        }
        jobs.append(_job(
            source,
            opening_id,
            selected.get("position") or selected.get("pageTitle"),
            location,
            selected["jobPublicationURL"],
            _dvinci_display_name(job_opening.get("department")),
            company=_dvinci_display_name(job_opening.get("company")),
            requisition_id=job_opening.get("reference"),
            mission=descriptions["mission"],
            requirements=descriptions["requirements"],
            benefits=descriptions["benefits"],
        ))
    return AcquisitionResult(
        sorted(jobs, key=lambda job: job["source_job_id"])
    )


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
    "dvinci": dvinci,
}


def source_opt_in_enabled(source, environ=None):
    environment = os.environ if environ is None else environ
    if "production_opt_in_env" not in source:
        return True
    variable = source["production_opt_in_env"]
    return (
        isinstance(variable, str)
        and bool(variable)
        and environment.get(variable) == "1"
    )


def acquire(source, fetch=_get):
    if not source.get("enabled"):
        return AcquisitionResult([], "disabled", False, "source disabled")
    if not source_opt_in_enabled(source):
        variable = source["production_opt_in_env"]
        return AcquisitionResult(
            [], "incomplete", False,
            f"Production opt-in {variable} is not enabled; collection was not attempted",
        )
    if source["acquisition_mode"] == "manual_discovery":
        return AcquisitionResult([], "manual_discovery", False, source["manual_reason"])
    adapter = ADAPTERS.get(source.get("adapter"))
    if adapter is None:
        return AcquisitionResult([], "failed", False, f"unknown adapter: {source.get('adapter')}")
    try:
        result = adapter(source, fetch=fetch)
        if not result.jobs:
            status = "incomplete" if result.status == "success" else result.status
            return AcquisitionResult(
                [], status, False, result.reason or "adapter returned zero jobs"
            )
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
