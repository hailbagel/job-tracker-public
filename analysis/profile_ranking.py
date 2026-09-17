"""Deterministic, evidence-backed personalized ranking for job snapshots."""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import io
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = "1.0"
RUBRIC_VERSION = "1.0"
ROLE_FAMILIES = (
    "Construction Project Management",
    "Construction Superintendent / Field Execution",
    "Structural / Steel",
    "Mechanical Construction",
    "Facilities / Infrastructure",
    "Project Controls",
    "QA/QC",
    "Commissioning / Turnover",
    "Utilities / Power",
    "Tooling / Installation",
    "Other",
    "Not relevant",
)
FAMILY_TERMS = {
    "Construction Project Management": ("construction project manager", "construction manager", "project manager"),
    "Construction Superintendent / Field Execution": ("superintendent", "field execution", "field operations"),
    "Structural / Steel": ("structural", "steel", "ironworker"),
    "Mechanical Construction": ("mechanical construction", "mechanical engineer", "piping", "plumbing", "hvac"),
    "Facilities / Infrastructure": ("facilities", "infrastructure", "site development", "civil"),
    "Project Controls": ("project controls", "scheduler", "cost engineer", "estimator"),
    "QA/QC": ("quality assurance", "quality control", "qa/qc", "inspector"),
    "Commissioning / Turnover": ("commissioning", "turnover", "startup"),
    "Utilities / Power": ("utilities", "power", "electrical", "substation"),
    "Tooling / Installation": ("tooling", "installation", "equipment install"),
}
SOFTWARE_TERMS = ("primavera p6", "p6", "autocad", "revit", "bluebeam", "procore", "excel", "solidworks")
TRADE_TERMS = ("welding", "steel", "concrete", "piping", "plumbing", "electrical", "hvac", "rigging")
MATERIAL_FIELDS = (
    "title", "location", "department", "potentially_relevant", "basic_qualifications", "preferred_qualifications",
    "degree_rule", "experience_in_lieu", "work_authorization_signal", "itar_signal", "years",
    "trade_requirements", "software_requirements", "travel_expectations", "shift_expectations",
)


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _clean(value):
    return re.sub(r"\s+", " ", html.unescape(str(value or ""))).strip()


def _nullable(value):
    return _clean(value) or None


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _sha(value):
    return hashlib.sha256(_canonical(value).encode()).hexdigest()


def _load_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _read_csv(path):
    with Path(path).open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def validate_profile(profile):
    required = {"schema_version", "profile_id", "display_name", "evidence_version", "role_families", "capabilities", "eligibility"}
    missing = sorted(required - set(profile))
    if missing:
        raise ValueError(f"Profile missing required keys: {', '.join(missing)}")
    invalid = sorted(set(profile["role_families"]) - set(ROLE_FAMILIES))
    if invalid:
        raise ValueError(f"Unknown role families: {', '.join(invalid)}")
    for gate in ("work_authorization", "itar"):
        item = profile["eligibility"].get(gate)
        if not isinstance(item, dict) or item.get("status") not in {"verified", "unsupported", "unknown"}:
            raise ValueError(f"eligibility.{gate}.status must be verified, unsupported, or unknown")
        if item["status"] == "verified" and not item.get("evidence"):
            raise ValueError(f"eligibility.{gate} verified status requires evidence")
    for capability in profile["capabilities"]:
        if not capability.get("name") or not capability.get("keywords") or not capability.get("evidence"):
            raise ValueError("Every capability requires name, keywords, and evidence")
    return profile


def load_profile(path):
    return validate_profile(_load_json(path))


def split_qualifications(text):
    text = str(text or "").replace("\r", "\n")
    marker = re.compile(r"(?im)^\s*(?:[-–—*]\s*)?(basic qualifications?|minimum qualifications?|preferred qualifications?|additional requirements?)\s*:?[ \t]*$")
    matches = list(marker.finditer(text))
    if not matches:
        return _clean(text), None, None
    sections = {}
    for index, match in enumerate(matches):
        heading = match.group(1).lower()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        key = "preferred" if "preferred" in heading else "additional" if "additional" in heading else "basic"
        sections[key] = _clean(text[match.end():end])
    return sections.get("basic") or _clean(text), sections.get("preferred"), sections.get("additional")


def classify_family(title, text):
    title_l, text_l = _clean(title).lower(), _clean(text).lower()
    best = (0, "Not relevant")
    for family, terms in FAMILY_TERMS.items():
        title_score = sum(3 for term in terms if term in title_l)
        score = title_score + (sum(1 for term in terms if term in text_l) if title_score else 0)
        if score > best[0]:
            best = (score, family)
    if best[0]:
        return best[1]
    if any(term in title_l for term in ("manager", "engineer", "technician", "specialist")):
        return "Other"
    return "Not relevant"


def _excerpt(text, pattern):
    match = re.search(pattern, text or "", re.I)
    if not match:
        return None
    return _clean(text[max(0, match.start() - 80):min(len(text), match.end() + 140)])


def _signals(basic, additional):
    required = " ".join(filter(None, (basic, additional)))
    return (
        _excerpt(required, r"authorized to work|work authorization|sponsorship"),
        _excerpt(required, r"ITAR|U\.S\. person|United States person|U\.S\. citizen|lawful permanent resident"),
        _excerpt(required, r"(?:bachelor|master|associate|degree)[^.;\n]{0,180}"),
        _excerpt(required, r"experience[^.;\n]{0,100}(?:in lieu|instead of)|(?:in lieu|instead of)[^.;\n]{0,100}experience"),
    )


def _gate(name, requirement, item):
    if not requirement:
        return None
    return {
        "gate": name,
        "requirement_evidence": {"source": "job_posting", "section": "required qualifications", "excerpt": requirement},
        "candidate_status": item["status"],
        "candidate_evidence": item.get("evidence"),
    }


def _salary(text):
    values = re.findall(r"\$[\d,]+(?:\.\d+)?(?:\s*(?:-|–|to)\s*\$?[\d,]+(?:\.\d+)?)?(?:\s*/\s*(?:year|hour))?", text, re.I)
    return "; ".join(dict.fromkeys(_clean(value) for value in values)) or None


def _focus(family, status):
    if status in {"RED", "UNKNOWN"}:
        return "A"
    if family == "Construction Superintendent / Field Execution":
        return "B"
    if family in {"Construction Project Management", "Project Controls"}:
        return "C"
    return "B-C Hybrid"


def rank_job(job, details, profile):
    title, location = _clean(job.get("title")), _clean(job.get("location"))
    requirements = details.get("requirements") or ""
    mission, benefits = details.get("mission") or "", details.get("benefits") or ""
    basic, preferred, additional = split_qualifications(requirements)
    combined = " ".join(filter(None, (title, location, mission, basic, preferred, additional)))
    combined_l = combined.lower()
    family = classify_family(title, combined)
    relevant = family in profile["role_families"] and family != "Not relevant"
    work_signal, itar_signal, degree_rule, experience_in_lieu = _signals(basic, additional)
    gates = [
        _gate("work_authorization", work_signal, profile["eligibility"]["work_authorization"]),
        _gate("itar", itar_signal, profile["eligibility"]["itar"]),
        _gate("degree", degree_rule, profile["eligibility"].get("degree", {"status": "unknown", "evidence": None})),
    ]
    gates = [gate for gate in gates if gate]
    score, reasons = (45, []) if relevant else (0, [])
    if relevant:
        reasons.append({"reason": "Role family is configured as an interest", "job_evidence": title, "candidate_evidence": {"source": f"profile:{profile['profile_id']}", "evidence_version": profile["evidence_version"]}})
    for capability in profile["capabilities"]:
        matched = sorted({word for word in capability["keywords"] if word.lower() in combined_l})
        if matched:
            score += min(10, 4 + len(matched) * 2)
            reasons.append({"reason": capability["name"], "job_evidence": matched, "candidate_evidence": capability["evidence"]})
    if any(place.lower() in location.lower() for place in profile.get("preferred_locations", [])):
        score += 8
        reasons.append({"reason": "Preferred location", "job_evidence": location, "candidate_evidence": {"source": f"profile:{profile['profile_id']}", "field": "preferred_locations"}})
    score = min(score, 100)
    gate_statuses = {gate["candidate_status"] for gate in gates}
    if not relevant or "unsupported" in gate_statuses:
        status = "RED"
    elif "unknown" in gate_statuses:
        status = "UNKNOWN"
    elif score >= int(profile.get("strong_match_threshold", 70)):
        status = "GREEN"
    else:
        status = "YELLOW"
    soft_gaps = [{"requirement": preferred, "source": "job_posting", "section": "preferred qualifications"}] if preferred else []
    years_found = [int(value) for value in re.findall(r"\b(\d{1,2})\+?\s+years?\b", basic.lower())]
    return {
        "job_id": _nullable(job.get("id")) or _nullable(job.get("job_id")) or _clean(job.get("link")),
        "requisition_id": _nullable(job.get("requisition_id")),
        "title": title,
        "location": location,
        "url": _clean(job.get("link") or job.get("url")),
        "first_published": _nullable(job.get("first_published")),
        "updated_at": _nullable(job.get("updated_at")),
        "department": _nullable(job.get("department")),
        "role_family": family,
        "potentially_relevant": relevant,
        "fit_score": score,
        "fit_reasons": reasons,
        "hard_gates": gates,
        "soft_gaps": soft_gaps,
        "degree_rule": degree_rule,
        "experience_in_lieu": experience_in_lieu,
        "work_authorization_signal": work_signal,
        "itar_signal": itar_signal,
        "recommended_profile_focus": _focus(family, status),
        "status": status,
        "basic_qualifications": _nullable(basic),
        "preferred_qualifications": _nullable(preferred),
        "years": min(years_found) if years_found else None,
        "trade_requirements": [term for term in TRADE_TERMS if term in combined_l],
        "software_requirements": [term for term in SOFTWARE_TERMS if term in combined_l],
        "travel_expectations": _excerpt(combined, r"travel[^.;\n]{0,120}"),
        "shift_expectations": _excerpt(combined, r"(?:shift|weekend|overtime)[^.;\n]{0,120}"),
        "salary": _salary(" ".join((requirements, benefits))),
        "evidence_provenance": {
            "job": {"source": "public_job_posting", "url": _clean(job.get("link") or job.get("url")), "detail_snapshot": None},
            "profile": {"profile_id": profile["profile_id"], "evidence_version": profile["evidence_version"]},
        },
    }


def _sort(records):
    return sorted(records, key=lambda row: (-row["fit_score"], row["title"].casefold(), row["location"].casefold(), str(row["job_id"]), row["url"]))


def _material(record):
    return {field: record.get(field) for field in MATERIAL_FIELDS}


def _changes(previous, current):
    if previous is None:
        return [], [], [], "First generated feed; no prior personalized snapshot was available for comparison."
    old = {str(row["job_id"]): row for row in previous.get("rankings", []) if row.get("potentially_relevant")}
    new = {str(row["job_id"]): row for row in current if row.get("potentially_relevant")}
    added = [new[key] for key in sorted(new.keys() - old.keys())]
    removed = [old[key] for key in sorted(old.keys() - new.keys())]
    changed = [new[key] for key in sorted(new.keys() & old.keys()) if _material(new[key]) != _material(old[key])]
    return _sort(added), _sort(changed), _sort(removed), None


def _counts(records):
    relevant = [row for row in records if row["potentially_relevant"]]
    return {
        "scanned": len(records),
        "potentially_relevant": len(relevant),
        "strong_match": sum(row["status"] == "GREEN" for row in relevant),
        "louisiana_pecan_island": sum(bool(re.search(r"louisiana|pecan island", row["location"], re.I)) for row in relevant),
    }


def _csv_bytes(records):
    fields = list(records[0]) if records else ["job_id", "requisition_id", "title", "location", "url", "role_family", "fit_score", "status"]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    for record in records:
        writer.writerow({key: _canonical(value) if isinstance(value, (dict, list)) else value for key, value in record.items()})
    return output.getvalue().encode()


def _md(document):
    meta, counts = document["metadata"], document["metadata"]["counts"]
    lines = [
        f"# SpaceX targets — {meta['profile_display_name']}", "",
        f"Generated: {meta['generated_at']}", f"Source snapshot observed: {meta['source_snapshot_observed_at']}",
        f"Source data changed: {meta['source_data_changed_at']}", "", "Coverage: complete", "",
        f"Scanned: {counts['scanned']} | Potentially relevant: {counts['potentially_relevant']} | Strong: {counts['strong_match']} | Louisiana/Pecan Island: {counts['louisiana_pecan_island']}", "",
        "GREEN requires direct candidate evidence for every detected eligibility gate. UNKNOWN never qualifies as a verified strong target.", "",
    ]
    if meta.get("history_limitation"):
        lines.extend((f"History limitation: {meta['history_limitation']}", ""))
    sections = (("Top 25", "top_25"), ("Verified strong targets (up to 10)", "verified_strong_targets"), ("Louisiana / Pecan Island", "louisiana_subset"), ("New relevant", "new_relevant"), ("Materially changed relevant", "materially_changed_relevant"), ("Removed relevant", "removed_relevant"))
    for heading, key in sections:
        lines.extend((f"## {heading}", ""))
        rows = document[key]
        lines.extend([f"- [{row['title']}]({row['url']}) — {row['location']} — {row['status']} {row['fit_score']} — `{row['job_id']}`" for row in rows] or ["_None._"])
        lines.append("")
    return ("\n".join(lines).rstrip() + "\n").encode()


def _atomic_batch(files):
    staged = []
    try:
        for path, content in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            handle = tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False)
            with handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            staged.append((Path(handle.name), path))
        for source, destination in staged:
            os.replace(source, destination)
    finally:
        for source, _ in staged:
            source.unlink(missing_ok=True)


def generate(profile_path, data_dir="data/spacex", output_dir=None, generated_at=None):
    profile, data_dir = load_profile(profile_path), Path(data_dir)
    acquisition = _load_json(data_dir / "processed" / "acquisition.json")
    jobs = _read_csv(data_dir / "processed" / "jobs_latest.csv")
    if not acquisition.get("coverage_complete") or acquisition.get("records_written") != len(jobs) or not jobs:
        raise RuntimeError("SpaceX acquisition is incomplete; preserving the previous personalized feed")
    details_path = data_dir / "processed" / "job_details.csv"
    details = {row.get("link"): row for row in _read_csv(details_path)} if details_path.exists() else {}
    records = _sort([rank_job(job, details.get(job.get("link"), {}), profile) for job in jobs])
    slug = re.sub(r"[^a-z0-9_-]+", "-", profile["profile_id"].lower()).strip("-")
    output_dir = Path(output_dir or data_dir / "exports" / slug)
    json_path, csv_path, md_path = (output_dir / "spacex_targets.json", output_dir / "spacex_targets.csv", output_dir / "spacex_targets.md")
    previous = _load_json(json_path) if json_path.exists() else None
    input_hash = _sha({
        "schema_version": SCHEMA_VERSION,
        "rubric_version": RUBRIC_VERSION,
        "profile_hash": _sha(profile),
        "source_data_hash": acquisition.get("data_hash"),
    })
    if previous and previous.get("metadata", {}).get("input_hash") == input_hash:
        return {"changed": False, "paths": [json_path, csv_path, md_path], "document": previous}
    added, changed, removed, limitation = _changes(previous, records)
    relevant = [row for row in records if row["potentially_relevant"]]
    semantic = {
        "schema_version": SCHEMA_VERSION, "rubric_version": RUBRIC_VERSION, "profile_hash": _sha(profile),
        "source_data_hash": acquisition.get("data_hash"), "rankings": records,
        "new_relevant": added, "materially_changed_relevant": changed, "removed_relevant": removed,
    }
    semantic_hash = _sha(semantic)
    document = {
        "schema_version": SCHEMA_VERSION,
        "metadata": {
            "generated_at": generated_at or _now(), "source_snapshot_observed_at": acquisition.get("observed_at"),
            "source_data_changed_at": acquisition.get("data_changed_at"), "coverage_complete": True,
            "profile_id": profile["profile_id"], "profile_display_name": profile["display_name"],
            "profile_evidence_version": profile["evidence_version"], "rubric_version": RUBRIC_VERSION,
            "input_hash": input_hash,
            "semantic_hash": semantic_hash, "counts": _counts(records), "history_limitation": limitation,
        },
        "rankings": records, "top_25": relevant[:25],
        "verified_strong_targets": [row for row in relevant if row["status"] == "GREEN"][:10],
        "louisiana_subset": [row for row in relevant if re.search(r"louisiana|pecan island", row["location"], re.I)],
        "new_relevant": added, "materially_changed_relevant": changed, "removed_relevant": removed,
    }
    _atomic_batch({
        json_path: (json.dumps(document, indent=2, ensure_ascii=False, sort_keys=True) + "\n").encode(),
        csv_path: _csv_bytes(records), md_path: _md(document),
    })
    return {"changed": True, "paths": [json_path, csv_path, md_path], "document": document}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate evidence-backed SpaceX profile targets")
    parser.add_argument("company", nargs="?", choices=["spacex"], help="Compatibility with the normal company pipeline.")
    parser.add_argument("--profile", default=os.environ.get("JOB_TRACKER_PROFILE_PATH", "configs/private_profiles/patrick.json"))
    parser.add_argument("--data-dir", default="data/spacex")
    parser.add_argument("--output-dir")
    parser.add_argument("--require-profile", action="store_true")
    args = parser.parse_args(argv)
    if not Path(args.profile).exists():
        message = f"Profile not provisioned: {args.profile}"
        if args.require_profile:
            parser.error(message)
        print(f"[profile ranking skipped] {message}")
        return 0
    result = generate(args.profile, args.data_dir, args.output_dir)
    print(f"SpaceX personalized targets {'updated' if result['changed'] else 'unchanged (preserved byte-for-byte)'}")
    for path in result["paths"]:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
