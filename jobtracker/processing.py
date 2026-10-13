from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from jobtracker.acquisition import acquisition_metadata


LATEST_FIELDS = (
    "id", "source_id", "source_job_id", "title", "location", "company",
    "department", "link", "requisition_id", "first_published", "updated_at",
    "scrape_timestamp",
)
DETAIL_FIELDS = LATEST_FIELDS + ("mission", "requirements", "benefits")
COMMON_OUTPUTS = ("jobs_latest.csv", "job_details.csv", "job_history.csv", "job_changes.csv", "department_summary.csv", "location_summary.csv")


def _read(path):
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))
    except FileNotFoundError:
        return []


def _write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", dir=path.parent, delete=False)
    temporary = Path(handle.name)
    try:
        with handle:
            writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _write_json(path, document):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False)
    temporary = Path(handle.name)
    try:
        with handle:
            json.dump(document, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def record_status(
    data_root,
    source,
    result,
    observed_at=None,
    *,
    pending_history_reset_from=None,
):
    metadata = acquisition_metadata(source, result, observed_at)
    if pending_history_reset_from:
        metadata["pending_history_reset_from"] = pending_history_reset_from
    _write_json(Path(data_root) / source["id"] / "processed" / "acquisition.json", metadata)
    return metadata


def _qualified_id(source_id, value):
    value = str(value or "").strip()
    if not value:
        return ""
    prefix = f"{source_id}:"
    return value if value.startswith(prefix) else f"{prefix}{value}"


def _row_id(source_id, row, ids_by_link=None, native_ids_by_link=None):
    for field in ("id", "source_job_id", "offer_uuid", "external_id"):
        value = row.get(field)
        if str(value or "").strip():
            return _qualified_id(source_id, value)
    link = str(row.get("link") or "").strip()
    if not link:
        return ""
    if ids_by_link and link in ids_by_link:
        return ids_by_link[link]
    if native_ids_by_link and link in native_ids_by_link:
        return _qualified_id(source_id, native_ids_by_link[link])
    suffix = hashlib.sha256(link.encode()).hexdigest()[:16]
    return f"{source_id}:{suffix}"


CHANGE_FIELDS = ("id", "source_id", "change", "title", "location", "observed_at")


def _canonical_change_rows(source_id, rows):
    migrated = []
    for row in rows:
        change = str(row.get("change") or row.get("change_type") or "").strip()
        if not change or change.lower() == "no_changes":
            continue
        migrated.append({
            "id": str(row.get("id") or "").strip(),
            "source_id": str(row.get("source_id") or source_id).strip(),
            "change": change.lower(),
            "title": str(row.get("title") or "").strip(),
            "location": str(row.get("location") or "").strip(),
            "observed_at": str(
                row.get("observed_at") or row.get("timestamp") or row.get("date") or ""
            ).strip(),
        })
    return migrated


def _deduplicate_changes(rows):
    unique = []
    seen = set()
    for row in rows:
        key = tuple(str(row.get(field) or "") for field in CHANGE_FIELDS)
        if key not in seen:
            seen.add(key)
            unique.append(dict(zip(CHANGE_FIELDS, key)))
    return unique


def process_success(
    data_root,
    source,
    result,
    observed_at=None,
    *,
    write_status=True,
    preserve_change_history=False,
    reset_history=False,
):
    if not result.coverage_complete or result.status != "success" or not result.jobs:
        raise ValueError("Only non-empty complete acquisitions may update normalized datasets")
    observed_at = observed_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    today = observed_at[:10]
    processed = Path(data_root) / source["id"] / "processed"
    previous_rows = [] if reset_history else _read(processed / "jobs_latest.csv")
    previous_details = [] if reset_history else _read(processed / "job_details.csv")
    native_ids_by_link = {}
    for row in previous_details:
        link = str(row.get("link") or "").strip()
        native_id = next((
            str(row.get(field) or "").strip()
            for field in ("source_job_id", "offer_uuid", "external_id")
            if str(row.get(field) or "").strip()
        ), "")
        if link and native_id:
            native_ids_by_link[link] = native_id
    previous_link_ids = {
        str(row.get("link") or "").strip(): _row_id(
            source["id"], row, native_ids_by_link=native_ids_by_link
        )
        for row in previous_rows
        if row.get("link")
    }
    previous = {}
    for row in previous_rows:
        job_id = _row_id(source["id"], row, native_ids_by_link=native_ids_by_link)
        if not job_id:
            raise ValueError("Cannot preserve a previous job without an id or link")
        previous[job_id] = row

    history = {}
    history_rows = [] if reset_history else _read(processed / "job_history.csv")
    for row in history_rows:
        link = str(row.get("link") or "").strip()
        job_id = (
            _qualified_id(source["id"], native_ids_by_link[link])
            if link in native_ids_by_link
            else _row_id(source["id"], row, previous_link_ids)
        )
        if not job_id:
            raise ValueError("Cannot preserve a history record without an id or link")
        migrated = dict(row, id=job_id)
        existing = history.get(job_id)
        if existing:
            first_seen = [
                value for value in (existing.get("first_seen"), migrated.get("first_seen"))
                if value
            ]
            last_seen = [
                value for value in (existing.get("last_seen"), migrated.get("last_seen"))
                if value
            ]
            if last_seen and max(last_seen) == migrated.get("last_seen"):
                existing = migrated
            existing["first_seen"] = min(first_seen) if first_seen else ""
            existing["last_seen"] = max(last_seen) if last_seen else ""
            history[job_id] = existing
        else:
            history[job_id] = migrated

    latest, details, changes = [], [], []
    for job in result.jobs:
        row = {field: job.get(field, "") for field in DETAIL_FIELDS}
        row["scrape_timestamp"] = observed_at
        job_id = _qualified_id(source["id"], row.get("id"))
        if not job_id or not row["title"] or not row["link"]:
            raise ValueError("Successful acquisitions require every job to have an id, title, and link")
        row["id"] = job_id
        row["source_id"] = source["id"]
        latest.append({field: row.get(field, "") for field in LATEST_FIELDS})
        details.append({field: row.get(field, "") for field in DETAIL_FIELDS})
        old = previous.get(job_id)
        existing = history.get(job_id, {})
        if old is None:
            change = "reactivated" if existing.get("active") == "False" else "new"
        else:
            change = "changed" if any(
                old.get(key, "") != str(row.get(key, ""))
                for key in ("title", "location", "department", "link")
            ) else None
        if change:
            changes.append({"id": job_id, "source_id": source["id"], "change": change, "title": row["title"], "location": row["location"], "observed_at": observed_at})
        history[job_id] = dict(row, first_seen=existing.get("first_seen", today), last_seen=today, active="True")
    current_ids = {row["id"] for row in latest}
    for job_id, old in previous.items():
        if job_id not in current_ids:
            changes.append({"id": job_id, "source_id": source["id"], "change": "removed", "title": old.get("title", ""), "location": old.get("location", ""), "observed_at": observed_at})
            if job_id in history:
                history[job_id]["active"] = "False"
    if preserve_change_history and not reset_history:
        changes = _deduplicate_changes(
            _canonical_change_rows(source["id"], _read(processed / "job_changes.csv"))
            + changes
        )
    _write_csv(processed / "jobs_latest.csv", LATEST_FIELDS, latest)
    _write_csv(processed / "job_details.csv", DETAIL_FIELDS, details)
    history_fields = DETAIL_FIELDS + ("first_seen", "last_seen", "active")
    _write_csv(processed / "job_history.csv", history_fields, sorted(history.values(), key=lambda row: row.get("id", "")))
    _write_csv(processed / "job_changes.csv", CHANGE_FIELDS, changes)
    for key, filename in (("department", "department_summary.csv"), ("location", "location_summary.csv")):
        counts = Counter(row[key] for row in latest)
        rows = [{key: name, "count": count} for name, count in sorted(counts.items())]
        rows.append({key: "TOTAL", "count": len(latest)})
        _write_csv(processed / filename, (key, "count"), rows)
    if write_status:
        return record_status(data_root, source, result, observed_at)
    return None
