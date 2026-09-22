from __future__ import annotations

import json
from pathlib import Path

from jobtracker.acquisition import acquire
from jobtracker.processing import process_success, record_status
from jobtracker.registry import get_source, sources


def run_source(source, data_root="data", fetch=None):
    kwargs = {"fetch": fetch} if fetch is not None else {}
    result = acquire(source, **kwargs)
    if result.status == "success" and result.coverage_complete:
        metadata = process_success(data_root, source, result)
    else:
        metadata = record_status(data_root, source, result)
    return metadata


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
