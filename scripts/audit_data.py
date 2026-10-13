#!/usr/bin/env python3
"""Read-only audit for tracked Job Tracker data/. No network or file changes."""
from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
COMMON = ("jobs_latest.csv", "job_details.csv", "job_history.csv", "job_changes.csv", "department_summary.csv", "location_summary.csv")
LATEST = ("id", "source_id", "source_job_id", "title", "location", "company", "department", "link", "requisition_id", "first_published", "updated_at", "scrape_timestamp")
DETAIL = LATEST + ("mission", "requirements", "benefits")
HISTORY = DETAIL + ("first_seen", "last_seen", "active")
CHANGE = ("id", "source_id", "change", "title", "location", "observed_at")
issues: list[tuple[str,str]] = []

def issue(level: str, message: str) -> None:
    issues.append((level, message))
    print(f"{level}: {message}")

def read_csv(path: Path) -> list[dict[str,str]] | None:
    if not path.is_file():
        issue("FAIL", f"missing file: {path.relative_to(ROOT)}")
        return None
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if not reader.fieldnames:
                issue("FAIL", f"empty header: {path.relative_to(ROOT)}")
                return None
            rows = list(reader)
            if any(None in row or any(value is None for value in row.values()) for row in rows):
                issue("FAIL", f"malformed CSV row: {path.relative_to(ROOT)}")
            return rows
    except (OSError, UnicodeError, csv.Error) as exc:
        issue("FAIL", f"cannot parse {path.relative_to(ROOT)}: {exc}")
        return None

def read_json(path: Path) -> dict | None:
    try:
        with path.open(encoding="utf-8") as stream:
            value = json.load(stream)
        if not isinstance(value, dict):
            raise ValueError("expected JSON object")
        return value
    except (OSError, UnicodeError, ValueError) as exc:
        issue("FAIL", f"invalid JSON at {path.relative_to(ROOT)}: {exc}")
        return None

def check_headers(path: Path, expected: tuple[str, ...]) -> None:
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            actual = next(csv.reader(stream), [])
        if tuple(actual) != expected:
            issue("FAIL", f"schema mismatch: {path.relative_to(ROOT)}")
    except (OSError, UnicodeError, csv.Error) as exc:
        issue("FAIL", f"header unreadable: {path.relative_to(ROOT)}: {exc}")

def unique(values: list[str], name: str) -> None:
    if len(values) != len(set(values)):
        issue("FAIL", f"duplicate {name}: {len(values) - len(set(values))}")

def inspect_source(source_id: str, status: dict) -> int:
    base = DATA / source_id / "processed"
    result = status.get("status")
    complete = status.get("coverage_complete") is True
    if result != "success" or not complete:
        issue("WARN", f"{source_id}: failed/incomplete collector ({status.get('reason')}); existing files are STALE")
        if status.get("records_written", 0) != 0:
            issue("FAIL", f"{source_id}: failed source claims new records")
        return 0
    paths = {name: base / name for name in COMMON}
    for filename in COMMON:
        check_headers(paths[filename], {"jobs_latest.csv": LATEST, "job_details.csv": DETAIL,
            "job_history.csv": HISTORY, "job_changes.csv": CHANGE,
            "department_summary.csv": ("department", "count"),
            "location_summary.csv": ("location", "count")}[filename])
    loaded = {n: read_csv(p) for n,p in paths.items()}
    if any(value is None for value in loaded.values()):
        return 0
    latest = loaded["jobs_latest.csv"]
    detail = loaded["job_details.csv"]
    history = loaded["job_history.csv"]
    changes = loaded["job_changes.csv"]
    ids = {row["id"] for row in latest}
    links = {row["link"] for row in latest}
    unique([row["id"] for row in latest], f"{source_id} current IDs")
    unique([row["link"] for row in latest], f"{source_id} current URLs")
    unique([row["id"] for row in history], f"{source_id} history IDs")
    unique([row["id"] for row in detail], f"{source_id} detail IDs")
    if not latest or int(status.get("records_written", -1)) != len(latest):
        issue("FAIL", f"{source_id}: status records_written differs from {len(latest)} current jobs")
    if {row["id"] for row in detail} != ids or {row["link"] for row in detail} != links:
        issue("FAIL", f"{source_id}: current jobs and detail rows do not match")
    if any(not row["id"].startswith(source_id + ":") or row["source_id"] != source_id or not row["title"] or not row["link"] for row in latest):
        issue("FAIL", f"{source_id}: empty/malformed job key, title or URL")
    active = {row["id"] for row in history if row["active"].lower() == "true"}
    if active != ids:
        issue("FAIL", f"{source_id}: active history IDs differ from latest ({len(active)} vs {len(ids)})")
    if any(row["first_seen"] > row["last_seen"] or row["active"].lower() not in ("true", "false") for row in history):
        issue("FAIL", f"{source_id}: invalid history dates/active flag")
    if any(row.get("source_id") != source_id or row.get("change") not in ("new", "changed", "removed", "reactivated") for row in changes):
        issue("FAIL", f"{source_id}: invalid source or change event")
    for field in ("department", "location"):
        rows = loaded[field + "_summary.csv"]
        totals = [row for row in rows if row[field] == "TOTAL"]
        groups = {row[field]: int(row["count"]) for row in rows if row[field] != "TOTAL"}
        expected = Counter(row.get(field, "") for row in latest)
        if len(totals) != 1 or int(totals[0]["count"]) != len(latest) or groups != expected:
            issue("FAIL", f"{source_id}: {field} summary disagrees with current data (TOTAL must be excluded from group sums)")
    blanks = sum(not (row["mission"].strip() or row["requirements"].strip() or row["benefits"].strip()) for row in detail)
    if blanks:
        issue("WARN", f"{source_id}: {blanks}/{len(detail)} detail rows contain no description, requirements, or benefits")
    placeholders = sum(row["title"].strip().upper() == "APPLY NOW" or row["location"].strip().lower() == "unknown" for row in latest)
    if placeholders:
        issue("FAIL", f"{source_id}: {placeholders} jobs contain old placeholder title/location")
    acquisition_path = base / "acquisition.json"
    if acquisition_path.is_file():
        acq = read_json(acquisition_path)
        if acq and (acq.get("status") != "success" or acq.get("coverage_complete") is not True or acq.get("records_written") != len(latest)):
            issue("FAIL", f"{source_id}: acquisition.json inconsistent with latest jobs")
        if acq and acq.get("adapter") and status.get("adapter") != acq.get("adapter"):
            issue("FAIL", f"{source_id}: acquisition adapter differs from source_status")
    print(f"CHECKED: {source_id}: {len(latest)} current, {len(detail)} details, {len(history)} history, {len(changes)} change events")
    return len(latest)

def inspect_feed(path: Path, expected: int, source_totals: dict[str,int], *, spacex_only: bool) -> None:
    feed_json = read_json(path / "patrick_targets.json")
    csv_rows = read_csv(path / "patrick_targets.csv")
    md = path / "patrick_targets.md"
    if not md.is_file() or md.stat().st_size == 0:
        issue("FAIL", f"missing/empty feed Markdown: {md.relative_to(ROOT)}")
    if feed_json is None or csv_rows is None:
        return
    rankings = feed_json.get("rankings")
    if not isinstance(rankings, list):
        issue("FAIL", f"{path.relative_to(ROOT)}: rankings must be an array")
        return
    if len(rankings) != len(csv_rows) or len(rankings) != expected:
        issue("FAIL", f"{path.relative_to(ROOT)}: JSON/CSV ranking count mismatch ({len(rankings)} vs {len(csv_rows)} vs {expected})")
    json_ids = [row.get("job_id") for row in rankings]
    csv_ids = [row.get("job_id") for row in csv_rows]
    unique(json_ids, f"{path.relative_to(ROOT)} ranking IDs")
    if json_ids != csv_ids:
        issue("FAIL", f"{path.relative_to(ROOT)}: JSON/CSV job_id order does not match")
    counts = feed_json.get("metadata", {}).get("counts", {})
    if counts.get("scanned") != expected:
        issue("FAIL", f"{path.relative_to(ROOT)}: metadata scanned count differs from input")
    if not spacex_only:
        breakdown = Counter(row.get("source_id") for row in rankings)
        if breakdown != Counter(source_totals):
            issue("FAIL", f"{path.relative_to(ROOT)}: source distribution differs from successful Patrick contributors ({dict(breakdown)})")
    print(f"CHECKED: {path.relative_to(ROOT)}: {len(rankings)} JSON/CSV ranking rows in order")

def main() -> int:
    if not DATA.is_dir():
        raise SystemExit("STOP: data/ directory missing")
    try:
        sha = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        sha = "unknown"
    print(f"READ-ONLY DATA AUDIT (git={sha})")
    registry = read_json(ROOT / "configs/sources.json")
    status = read_json(DATA / "source_status.json")
    if registry is None or status is None:
        return 1
    configured = {s["id"]: s for s in registry.get("sources", []) if s.get("enabled") and s.get("acquisition_mode") != "manual_discovery"}
    published = {s["source_id"]: s for s in status.get("sources", [])}
    if configured.keys() != published.keys():
        issue("FAIL", f"registry vs source_status mismatch: configured={sorted(configured)}, published={sorted(published)}")
    totals = {sid: inspect_source(sid, s) for sid,s in published.items()}
    contributors = status.get("publication", {}).get("published_feed_contributors", [])
    expected_contributors = {sid: totals[sid] for sid in contributors if sid in totals}
    if len(expected_contributors) != len(contributors):
        issue("FAIL", "published contributor not present in status")
    if any(not published[sid].get("coverage_complete") for sid in expected_contributors):
        issue("FAIL", "failed source included in published contributors")
    inspect_feed(DATA / "patrick" / "processed", sum(expected_contributors.values()), expected_contributors, spacex_only=False)
    inspect_feed(DATA / "spacex" / "processed", totals.get("spacex", 0), {"spacex": totals.get("spacex", 0)}, spacex_only=True)
    # Check even preserved stale legacy files for basic parseability.
    for file in sorted(DATA.rglob("*")):
        if not file.is_file():
            continue
        parts = file.relative_to(DATA).parts
        source_id = parts[0] if len(parts) >= 3 else None
        stale_or_extra = source_id in published and not published[source_id].get("coverage_complete")
        extra_legacy = file.name == "jobs_structured.csv"
        if file.suffix.lower() == ".csv" and (stale_or_extra or extra_legacy):
            extra_rows = read_csv(file)
            if extra_rows is not None:
                print(f"INFO: legacy/non-authoritative {file.relative_to(ROOT)}: {len(extra_rows)} rows")
        elif file.suffix.lower() == ".json" and stale_or_extra:
            read_json(file)
        elif file.suffix.lower() not in (".csv", ".json", ".md"):
            issue("WARN", f"unexpected file extension: {file.relative_to(ROOT)}")
    errors = sum(level == "FAIL" for level, _ in issues)
    warnings = sum(level == "WARN" for level, _ in issues)
    print(f"AUDIT_RESULT FAIL={errors} WARN={warnings} CHECKED_FILES={sum(p.is_file() for p in DATA.rglob('*'))}")
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
