from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from jobtracker.acquisition import AcquisitionResult, acquire
from jobtracker.processing import process_success, record_status
from jobtracker.registry import get_source, sources


def run_source(source, data_root="data", fetch=None):
    kwargs = {"fetch": fetch} if fetch is not None else {}
    result = acquire(source, **kwargs)
    reset_from_adapter = source.get("reset_history_on_adapter_change_from")
    reset_history = False
    acquisition_path = Path(data_root) / source["id"] / "processed" / "acquisition.json"
    if reset_from_adapter and acquisition_path.exists():
        previous_metadata = json.loads(acquisition_path.read_text(encoding="utf-8"))
        if not isinstance(previous_metadata, dict):
            raise ValueError(f"Invalid acquisition metadata: {acquisition_path}")
        reset_history = (
            source.get("adapter") != reset_from_adapter
            and (
                previous_metadata.get("pending_history_reset_from") == reset_from_adapter
                or previous_metadata.get("adapter") == reset_from_adapter
            )
        )

    if result.status == "success" and result.coverage_complete:
        metadata = process_success(
            data_root, source, result, reset_history=reset_history
        )
    else:
        metadata = record_status(
            data_root,
            source,
            result,
            pending_history_reset_from=reset_from_adapter if reset_history else None,
        )
    return metadata


def normalize_existing_provider(source, data_root="data", observed_at=None):
    processed = Path(data_root) / source["id"] / "processed"
    latest_path = processed / "jobs_latest.csv"
    details_path = processed / "job_details.csv"
    with latest_path.open(newline="", encoding="utf-8-sig") as handle:
        latest_rows = list(csv.DictReader(handle))
    if not latest_rows:
        raise ValueError(f"Existing provider produced no jobs: {latest_path}")

    if details_path.exists():
        with details_path.open(newline="", encoding="utf-8-sig") as handle:
            details_rows = list(csv.DictReader(handle))
    else:
        details_rows = []
    details_by_link = {
        str(row.get("link") or "").strip(): row
        for row in details_rows
        if row.get("link")
    }

    jobs = []
    seen_links = set()
    for row in latest_rows:
        title = str(row.get("title") or "").strip()
        link = str(row.get("link") or "").strip()
        if not title or not link or link in seen_links:
            raise ValueError(f"Existing provider returned an incomplete or duplicate job: {link!r}")
        seen_links.add(link)
        if link not in details_by_link:
            raise ValueError(
                f"Existing provider {source['id']} is missing a detail row for current job link: {link!r}"
            )
        details = details_by_link[link]
        native_id = next((
            str(value).strip()
            for value in (
                row.get("source_job_id"), row.get("id"),
                details.get("source_job_id"), details.get("offer_uuid"),
                details.get("external_id"),
            )
            if str(value or "").strip()
        ), "")
        if not native_id:
            native_id = hashlib.sha256(link.encode()).hexdigest()[:16]
        job_id = native_id if native_id.startswith(f"{source['id']}:") else f"{source['id']}:{native_id}"
        jobs.append({
            "id": job_id,
            "source_id": source["id"],
            "source_job_id": native_id.removeprefix(f"{source['id']}:"),
            "title": title,
            "location": str(row.get("location") or "").strip(),
            "company": str(row.get("company") or "").strip() or source["company"],
            "department": str(row.get("department") or "").strip(),
            "link": link,
            "requisition_id": str(row.get("requisition_id") or details.get("requisition_id") or "").strip(),
            "first_published": str(row.get("first_published") or details.get("first_published") or "").strip(),
            "updated_at": str(row.get("updated_at") or details.get("updated_at") or "").strip(),
            "mission": str(details.get("mission") or "").strip(),
            "requirements": str(details.get("requirements") or "").strip(),
            "benefits": str(details.get("benefits") or "").strip(),
        })

    return process_success(
        data_root,
        source,
        AcquisitionResult(jobs),
        observed_at,
        write_status=False,
        preserve_change_history=True,
    )


def run_registry(registry_path="configs/sources.json", data_root="data", source_ids=None, fetch=None):
    selected = sources(registry_path, enabled_only=True)
    if source_ids is not None:
        wanted = set(source_ids)
        selected = [source for source in selected if source["id"] in wanted]
    statuses = []
    for source in selected:
        if source["acquisition_mode"] == "existing_provider":
            continue
        statuses.append(run_source(source, data_root, fetch))
    path = Path(data_root) / "source_status.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"schema_version": 1, "sources": statuses}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return statuses


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run registry-backed public job acquisition")
    parser.add_argument("--registry", default="configs/sources.json")
    parser.add_argument("--data-root", default="data")
    parser.add_argument("--source", action="append", dest="source_ids")
    args = parser.parse_args(argv)
    statuses = run_registry(args.registry, args.data_root, args.source_ids)
    failed = [item for item in statuses if item["status"] in {"failed", "incomplete"}]
    for item in statuses:
        print(
            f"{item['source_id']}: {item['status']} "
            f"({item['records_written']} jobs; complete={item['coverage_complete']})"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
