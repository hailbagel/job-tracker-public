from __future__ import annotations

import csv
import json
import os
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from jobtracker.acquisition import acquisition_metadata


LATEST_FIELDS = ("id", "source_id", "source_job_id", "title", "location", "company", "department", "link", "scrape_timestamp")
DETAIL_FIELDS = LATEST_FIELDS + ("mission", "requirements", "benefits")
COMMON_OUTPUTS = ("jobs_latest.csv", "job_details.csv", "job_history.csv", "job_changes.csv", "department_summary.csv", "location_summary.csv")


def _read(path):
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))
    except (FileNotFoundError, csv.Error):
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


def record_status(data_root, source, result, observed_at=None):
    metadata = acquisition_metadata(source, result, observed_at)
    _write_json(Path(data_root) / source["id"] / "processed" / "acquisition.json", metadata)
    return metadata


def process_success(data_root, source, result, observed_at=None):
    if not result.coverage_complete or result.status != "success" or not result.jobs:
        raise ValueError("Only non-empty complete acquisitions may update normalized datasets")
    observed_at = observed_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    today = observed_at[:10]
    processed = Path(data_root) / source["id"] / "processed"
    previous = {row.get("id"): row for row in _read(processed / "jobs_latest.csv")}
    history = {row.get("id"): row for row in _read(processed / "job_history.csv")}
    latest, details, changes = [], [], []
    for job in result.jobs:
        row = dict(job, scrape_timestamp=observed_at)
        latest.append({field: row.get(field, "") for field in LATEST_FIELDS})
        details.append({field: row.get(field, "") for field in DETAIL_FIELDS})
        old = previous.get(row["id"])
        change = "new" if old is None else "changed" if any(old.get(key, "") != str(row.get(key, "")) for key in ("title", "location", "department", "link")) else None
        if change:
            changes.append({"id": row["id"], "source_id": source["id"], "change": change, "title": row["title"], "location": row["location"], "observed_at": observed_at})
        existing = history.get(row["id"], {})
        history[row["id"]] = dict(row, first_seen=existing.get("first_seen", today), last_seen=today, active="True")
    current_ids = {row["id"] for row in latest}
    for job_id, old in previous.items():
        if job_id not in current_ids:
            changes.append({"id": job_id, "source_id": source["id"], "change": "removed", "title": old.get("title", ""), "location": old.get("location", ""), "observed_at": observed_at})
            if job_id in history:
                history[job_id]["active"] = "False"
    _write_csv(processed / "jobs_latest.csv", LATEST_FIELDS, latest)
    _write_csv(processed / "job_details.csv", DETAIL_FIELDS, details)
    history_fields = DETAIL_FIELDS + ("first_seen", "last_seen", "active")
    _write_csv(processed / "job_history.csv", history_fields, sorted(history.values(), key=lambda row: row.get("id", "")))
    _write_csv(processed / "job_changes.csv", ("id", "source_id", "change", "title", "location", "observed_at"), changes)
    for key, filename in (("department", "department_summary.csv"), ("location", "location_summary.csv")):
        counts = Counter(row[key] for row in latest)
        rows = [{key: name, "count": count} for name, count in sorted(counts.items())]
        rows.append({key: "TOTAL", "count": len(latest)})
        _write_csv(processed / filename, (key, "count"), rows)
    return record_status(data_root, source, result, observed_at)
