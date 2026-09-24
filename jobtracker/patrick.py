from __future__ import annotations

import csv
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from analysis.profile_ranking import _changes, _counts, _sort, load_profile, rank_job


FEED_FILES = ("patrick_targets.csv", "patrick_targets.json", "patrick_targets.md")


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _atomic_write(path, content, *, binary=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    mode = "wb" if binary else "w"
    kwargs = {} if binary else {"encoding": "utf-8"}
    handle = tempfile.NamedTemporaryFile(mode, dir=path.parent, delete=False, **kwargs)
    temporary = Path(handle.name)
    try:
        with handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _public_record(record, source):
    item = dict(record)
    item["source_id"] = source["id"]
    item["company"] = source["company"]
    native_id = str(item.get("job_id") or item.get("url"))
    prefix = f"{source['id']}:"
    item["job_id"] = native_id if native_id.startswith(prefix) else prefix + native_id
    item["fit_reasons"] = [
        {"reason": reason.get("reason"), "job_evidence": reason.get("job_evidence")}
        for reason in item.get("fit_reasons", [])
    ]
    item["hard_gates"] = [
        {
            "gate": gate.get("gate"),
            "candidate_status": gate.get("candidate_status"),
            "requirement_evidence": gate.get("requirement_evidence"),
        }
        for gate in item.get("hard_gates", [])
    ]
    item["evidence_provenance"] = {"job": item.get("evidence_provenance", {}).get("job")}
    return item


def _source_rows(source, data_root):
    processed = Path(data_root) / source["id"] / "processed"
    acquisition_path = processed / "acquisition.json"
    try:
        acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
        jobs = _read_csv(processed / "jobs_latest.csv")
        details_rows = _read_csv(processed / "job_details.csv")
    except (OSError, csv.Error, json.JSONDecodeError) as exc:
        return [], {
            "source_id": source["id"],
            "company": source["company"],
            "status": "unavailable",
            "coverage_complete": False,
            "reason": str(exc),
            "jobs": 0,
        }
    complete = (
        acquisition.get("status", "success") == "success"
        and acquisition.get("coverage_complete") is True
        and acquisition.get("records_written") == len(jobs)
        and bool(jobs)
    )
    coverage = {
        "source_id": source["id"],
        "company": source["company"],
        "status": acquisition.get("status", "success"),
        "coverage_complete": complete,
        "reason": acquisition.get("reason"),
        "jobs": len(jobs) if complete else 0,
        "observed_at": acquisition.get("observed_at"),
        "acquisition_mode": source.get("acquisition_mode"),
        "adapter": source.get("adapter"),
    }
    if not complete:
        return [], coverage
    details = {row.get("link"): row for row in details_rows}
    return [(job, details.get(job.get("link"), {})) for job in jobs], coverage


def _csv_bytes(records):
    fields = (
        "source_id", "company", "job_id", "title", "location", "url", "role_family",
        "fit_score", "status", "fit_reasons", "hard_gates", "soft_gaps",
        "recommended_profile_focus",
    )
    import io
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    for record in records:
        writer.writerow({
            key: json.dumps(value, sort_keys=True, ensure_ascii=False) if isinstance(value, (list, dict)) else value
            for key, value in record.items()
        })
    return output.getvalue().encode()


def _markdown(document):
    meta = document["metadata"]
    counts = meta["counts"]
    lines = [
        "# Patrick Space/Rocket targets",
        "",
        f"Generated: {meta['generated_at']}",
        f"Scanned: {counts['scanned']} | Potentially relevant: {counts['potentially_relevant']} | Strong: {counts['strong_match']}",
        "",
        "## Source coverage",
        "",
    ]
    for item in meta["source_coverage"]:
        lines.append(
            f"- {item['company']} (`{item['source_id']}`): {item['status']}; "
            f"complete={str(item['coverage_complete']).lower()}; jobs={item['jobs']}"
        )
    sections = (
        ("Top 25", "top_25"),
        ("Strongest targets", "strongest_targets"),
        ("New relevant jobs", "new_relevant"),
        ("Materially changed jobs", "materially_changed_relevant"),
        ("Removed jobs", "removed_relevant"),
        ("SpaceX Louisiana / Pecan Island", "spacex_louisiana_subset"),
    )
    for heading, key in sections:
        lines.extend(("", f"## {heading}", ""))
        rows = document[key]
        if not rows:
            lines.append("_None._")
        for row in rows:
            reasons = ", ".join(item.get("reason") or "" for item in row["fit_reasons"]) or "none"
            gates = ", ".join(
                f"{item['gate']}={item['candidate_status']}" for item in row["hard_gates"]
            ) or "none"
            lines.extend((
                f"- [{row['company']}: {row['title']}]({row['url']}) — {row['location']} — "
                f"{row['status']} {row['fit_score']}",
                f"  - Role family: {row['role_family']}",
                f"  - Fit reasons: {reasons}",
                f"  - Hard gates: {gates}",
                f"  - Soft gaps: {json.dumps(row['soft_gaps'], ensure_ascii=False)}",
                f"  - Recommended profile focus: {row['recommended_profile_focus']}",
            ))
    return "\n".join(lines).rstrip() + "\n"


def generate_multi(
    profile_path, sources, data_root="data", output_dir="data/patrick/processed",
    generated_at=None, coverage_overrides=None,
):
    profile = load_profile(profile_path)
    output_dir = Path(output_dir)
    previous = None
    try:
        previous = json.loads((output_dir / "patrick_targets.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        pass
    records, coverage = [], []
    for source in sources:
        rows, item = _source_rows(source, data_root)
        override = (coverage_overrides or {}).get(source["id"])
        if override and not override.get("coverage_complete", False):
            rows = []
            item.update(override)
            item.update(source_id=source["id"], company=source["company"], jobs=0)
        coverage.append(item)
        for job, details in rows:
            records.append(_public_record(rank_job(job, details, profile), source))
    records = _sort(records)
    incomplete_sources = {
        item["source_id"] for item in coverage if not item["coverage_complete"]
    }
    comparable_previous = previous
    if previous is not None and incomplete_sources:
        comparable_previous = dict(previous)
        comparable_previous["rankings"] = [
            row for row in previous.get("rankings", [])
            if row.get("source_id") not in incomplete_sources
        ]
    added, changed, removed, limitation = _changes(comparable_previous, records)
    relevant = [row for row in records if row["potentially_relevant"]]
    counts = _counts(records)
    document = {
        "schema_version": "1.0",
        "metadata": {
            "generated_at": generated_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "coverage_complete": all(item["coverage_complete"] for item in coverage),
            "source_coverage": coverage,
            "counts": counts,
            "history_limitation": limitation,
        },
        "rankings": records,
        "top_25": relevant[:25],
        "strongest_targets": [row for row in relevant if row["status"] == "GREEN"][:10],
        "new_relevant": added,
        "materially_changed_relevant": changed,
        "removed_relevant": removed,
        "spacex_louisiana_subset": [
            row for row in relevant
            if row["source_id"] == "spacex" and re.search(r"louisiana|pecan island", row["location"], re.I)
        ],
    }
    json_bytes = (json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode()
    csv_bytes = _csv_bytes(records)
    markdown = _markdown(document).encode()
    _atomic_write(output_dir / "patrick_targets.json", json_bytes, binary=True)
    _atomic_write(output_dir / "patrick_targets.csv", csv_bytes, binary=True)
    _atomic_write(output_dir / "patrick_targets.md", markdown, binary=True)
    return document
