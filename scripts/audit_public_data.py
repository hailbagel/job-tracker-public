#!/usr/bin/env python3
"""Read-only conformity audit for versioned job-tracker data files."""
from __future__ import annotations

import csv
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ("jobs_latest.csv", "job_details.csv", "job_history.csv",
           "job_changes.csv", "department_summary.csv", "location_summary.csv")
failures = []
warnings = []

def report(level, message):
    print(f"[{level}] {message}", flush=True)
    (failures if level == "FAIL" else warnings).append(message)

def check(yes, message):
    if not yes:
        report("FAIL", message)

def read_csv(path, required=()):
    if not path.is_file():
        raise ValueError(f"missing {path.relative_to(ROOT)}")
    with path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        header = reader.fieldnames or []
        if not header or len(header) != len(set(header)):
            raise ValueError(f"invalid CSV header: {path.relative_to(ROOT)}")
        if not set(required).issubset(header):
            raise ValueError(f"missing required CSV columns: {path.relative_to(ROOT)}")
        rows = list(reader)
    if any(None in r or any(v is None for v in r.values()) for r in rows):
        raise ValueError(f"malformed CSV rows: {path.relative_to(ROOT)}")
    return rows

def verify_summary(source_id, jobs, summary, field):
    actual = Counter((r.get(field) or "").strip() for r in jobs)
    found = {}
    for row in summary:
        try:
            number = int(row["count"])
        except (TypeError, ValueError, KeyError):
            report("FAIL", f"{source_id}/{field} summary: invalid count")
            return
        group = row.get(field, "")
        check(group not in found, f"{source_id}/{field} summary: duplicate group {group!r}")
        found[group] = number
    check(found.pop("TOTAL", None) == len(jobs), f"{source_id}/{field} summary: TOTAL disagrees")
    check(found == dict(actual), f"{source_id}/{field} summary: groups disagree")

def check_feed(area, target):
    directory = DATA / area / "processed"
    try:
        document = json.loads((directory / "patrick_targets.json").read_text(encoding="utf-8"))
        rankings = document["rankings"]
        tabular = read_csv(directory / "patrick_targets.csv", ("job_id", "title"))
        human = (directory / "patrick_targets.md").read_text(encoding="utf-8")
        check(len(rankings) == len(tabular) == target, f"{area} feed: JSON/CSV count differs from {target}")
        check(all(str(j.get("job_id")) == str(c.get("job_id")) and j.get("title") == c.get("title")
                  for j, c in zip(rankings, tabular)), f"{area} feed: CSV/JSON order or identity differs")
        check(document.get("metadata", {}).get("counts", {}).get("scanned") == target,
              f"{area} feed: scanned metadata differs")
        check(f"Scanned: {target}" in human, f"{area} feed: markdown count differs")
        print(f"[CHECK] {area} feed: {len(rankings)} JSON and CSV records")
        return document
    except (OSError, UnicodeError, csv.Error, ValueError, KeyError) as error:
        report("FAIL", f"{area} feed: {error}")
        return {}

def main():
    registry = json.loads((ROOT / "configs/sources.json").read_text(encoding="utf-8"))
    status = json.loads((DATA / "source_status.json").read_text(encoding="utf-8"))
    automated = [s for s in registry["sources"] if s["enabled"] and s["acquisition_mode"] != "manual_discovery"]
    results = {s["source_id"]: s for s in status["sources"]}
    check(set(results) == {s["id"] for s in automated}, "source registry/status mismatch")
    succeeded = {k for k, v in results.items() if v.get("status") == "success" and v.get("coverage_complete") is True}
    check(set(status["publication"]["successful_sources"]) == succeeded, "successful_sources mismatch")
    check(set(status["publication"]["failed_or_incomplete_sources"]) == set(results) - succeeded,
          "failed source IDs mismatch")
    print("=== READ-ONLY DATA AUDIT ===", flush=True)
    for source in automated:
        sid = source["id"]
        folder = DATA / sid / "processed"
        files = {}
        for name in OUTPUTS:
            try:
                required = ("title", "location", "company", "department", "link") if name == "jobs_latest.csv" else (
                    ("title", "location", "company", "department", "link", "mission", "requirements", "benefits")
                    if name == "job_details.csv" else ())
                files[name] = read_csv(folder / name, required)
            except (OSError, UnicodeError, csv.Error, ValueError) as error:
                report("FAIL", f"{sid}/{name}: {error}")
        if len(files) != len(OUTPUTS):
            continue
        jobs, detail, history, changes, depts, places = [files[n] for n in OUTPUTS]
        if sid not in succeeded:
            report("WARN", f"{sid}: failed collection; {len(jobs)} preserved entries are STALE")
            continue
        print(f"[CHECK] {sid}: current={len(jobs)} detail={len(detail)} history={len(history)} changes={len(changes)}")
        check(len(jobs) > 0 and len(jobs) == results[sid].get("records_written"), f"{sid}: current/status count mismatch")
        ids = [r.get("id", "") for r in jobs]
        links = [r.get("link", "") for r in jobs]
        check(len(ids) == len(set(ids)) and all(x.startswith(sid + ":") for x in ids), f"{sid}: invalid or duplicate current IDs")
        check(len(links) == len(set(links)) and all(x.startswith(("https://", "http://")) for x in links),
              f"{sid}: invalid or duplicate current URLs")
        check(all(r.get("source_id") == sid for r in jobs), f"{sid}: source_id mismatch")
        check(all(r.get("title", "").strip().upper() not in ("", "APPLY NOW") for r in jobs),
              f"{sid}: blank/placeholder job title")
        missing_locations = sum(not r.get("location", "").strip() or r.get("location", "").strip().lower() == "unknown" for r in jobs)
        if missing_locations:
            report("WARN", f"{sid}: {missing_locations} jobs have unknown locations")
        by_id = {r.get("id"): r for r in detail}
        check(len(by_id) == len(detail) == len(jobs) and set(by_id) == set(ids), f"{sid}: current/detail IDs mismatch")
        check(all(by_id[k].get("link") == r.get("link") for k, r in zip(ids, jobs) if k in by_id),
              f"{sid}: current/detail links mismatch")
        no_text = sum(not any(row.get(col, "").strip() for col in ("mission", "requirements", "benefits")) for row in detail)
        if no_text:
            report("WARN", f"{sid}: {no_text}/{len(detail)} details lack all description fields")
        history_ids = [r.get("id") for r in history]
        check(len(history_ids) == len(set(history_ids)), f"{sid}: duplicate history IDs")
        if not history or not {"id", "active", "first_seen", "last_seen"}.issubset(history[0]):
            report("FAIL", f"{sid}: missing required history fields")
        else:
            active = {r["id"] for r in history if str(r.get("active", "")).lower() == "true"}
            check(active == set(ids), f"{sid}: active history IDs disagree with current")
            check(all(str(r.get("active", "")).lower() in ("true", "false") for r in history),
                  f"{sid}: history active flags invalid")
            check(all(not r.get("first_seen") or not r.get("last_seen") or r["first_seen"] <= r["last_seen"]
                      for r in history), f"{sid}: history first_seen/last_seen inconsistent")
        if changes:
            check({"id", "source_id", "change", "title", "location", "observed_at"}.issubset(changes[0]),
                  f"{sid}: change event schema invalid")
            check(all(r.get("source_id") == sid and r.get("change") in
                      ("new", "changed", "removed", "reactivated") for r in changes),
                  f"{sid}: change-event type or source invalid")
        verify_summary(sid, jobs, depts, "department")
        verify_summary(sid, jobs, places, "location")
        acquisition = folder / "acquisition.json"
        if acquisition.exists():
            item = json.loads(acquisition.read_text(encoding="utf-8"))
            check(item.get("status") == "success" and item.get("coverage_complete") is True
                  and item.get("records_written") == len(jobs), f"{sid}: acquisition metadata mismatch")
            if sid == "hyimpulse":
                check(item.get("adapter") == "personio_xml", "hyimpulse: wrong acquisition adapter")
    neura_aux = DATA / "neura/processed/jobs_structured.csv"
    if neura_aux.is_file():
        old = read_csv(neura_aux)
        current = read_csv(DATA / "neura/processed/jobs_latest.csv")
        if len(old) != len(current):
            report("WARN", f"NEURA auxiliary jobs_structured.csv={len(old)} vs current={len(current)}; review purpose")
    contributors = [s for s in automated if s.get("sector") == "Space/Rocket" and "patrick" in s.get("tags", [])]
    expected_counts = {s["id"]: results[s["id"]]["records_written"] for s in contributors}
    check(all(s["id"] in succeeded for s in contributors), "Patrick source contributor missing/failed")
    patrick = check_feed("patrick", sum(expected_counts.values()))
    check({r.get("source_id"): r.get("jobs") for r in
           patrick.get("metadata", {}).get("source_coverage", [])} == expected_counts,
          "Patrick feed source coverage disagrees with source status")
    check_feed("spacex", results["spacex"]["records_written"])
    try:
        tracked = set(subprocess.check_output(["git", "ls-files", "--", "data"], cwd=ROOT, text=True).splitlines())
        expected = {f"data/{s['id']}/processed/{n}" for s in automated for n in OUTPUTS}
        expected |= {f"data/{s['id']}/processed/acquisition.json" for s in automated
                     if s["acquisition_mode"] != "existing_provider"}
        expected |= {"data/spacex/processed/acquisition.json", "data/neura/processed/jobs_structured.csv",
                     "data/source_status.json"}
        expected |= {f"data/{x}/processed/patrick_targets.{ext}" for x in ("spacex", "patrick")
                     for ext in ("csv", "json", "md")}
        check(tracked == expected, f"tracked data paths differ: missing={sorted(expected-tracked)}, unexpected={sorted(tracked-expected)}")
        check(all("/raw/" not in x and "private" not in x.lower() and "/exports/" not in x for x in tracked),
              "raw, exports, or private paths tracked in data")
        print(f"[CHECK] tracked data files: {len(tracked)}")
    except (OSError, subprocess.CalledProcessError) as error:
        report("WARN", f"cannot enumerate tracked paths: {error}")
    print(f"=== AUDIT COMPLETE: {len(failures)} failures / {len(warnings)} warnings ===")
    return 2 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
