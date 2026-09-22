from __future__ import annotations

import json
from pathlib import Path


REQUIRED_FIELDS = {
    "id", "company", "careers_url", "country", "region", "sector",
    "acquisition_mode", "enabled", "priority", "tags",
}
ACQUISITION_MODES = {"existing_provider", "api", "ats", "web", "manual_discovery"}


class RegistryError(ValueError):
    pass


def load_registry(path="configs/sources.json"):
    path = Path(path)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RegistryError(f"Cannot load source registry {path}: {exc}") from exc
    if document.get("schema_version") != 1 or not isinstance(document.get("sources"), list):
        raise RegistryError("Source registry must have schema_version 1 and a sources array")
    seen = set()
    for index, source in enumerate(document["sources"]):
        missing = REQUIRED_FIELDS - set(source)
        if missing:
            raise RegistryError(f"Source {index} is missing fields: {', '.join(sorted(missing))}")
        source_id = source["id"]
        if source_id in seen:
            raise RegistryError(f"Duplicate source id: {source_id}")
        seen.add(source_id)
        if source["acquisition_mode"] not in ACQUISITION_MODES:
            raise RegistryError(f"Invalid acquisition mode for {source_id}: {source['acquisition_mode']}")
        if not isinstance(source["enabled"], bool) or not isinstance(source["tags"], list):
            raise RegistryError(f"Invalid enabled/tags types for {source_id}")
        if source["acquisition_mode"] != "manual_discovery" and not source.get("adapter"):
            raise RegistryError(f"Automated source {source_id} requires an adapter")
        if source["acquisition_mode"] == "manual_discovery" and not source.get("manual_reason"):
            raise RegistryError(f"Manual source {source_id} requires manual_reason")
    return document


def sources(path="configs/sources.json", *, enabled_only=False):
    items = load_registry(path)["sources"]
    return [item for item in items if item["enabled"]] if enabled_only else items


def get_source(source_id, path="configs/sources.json"):
    for source in sources(path):
        if source["id"] == source_id:
            return source
    raise RegistryError(f"Unknown source: {source_id}")
