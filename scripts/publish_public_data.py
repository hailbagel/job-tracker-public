#!/usr/bin/env python3
"""Collect, validate, version, and publish public datasets and Patrick's feed."""

from __future__ import annotations

import csv
import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

from jobtracker.patrick import generate_multi
from jobtracker.registry import RegistryError, sources


REQUIRED_PROVIDERS = ("neura", "spacex", "tesla", "jacobs")
COMMON_OUTPUTS = (
    "department_summary.csv", "job_changes.csv", "job_details.csv",
    "job_history.csv", "jobs_latest.csv", "location_summary.csv",
)
PUBLIC_FEED_FILES = ("patrick_targets.csv", "patrick_targets.json", "patrick_targets.md")
JOB_FIELDS = {"title", "location", "company", "department", "link"}
DETAIL_FIELDS = JOB_FIELDS | {"mission", "requirements", "benefits"}


def output_allowlist():
    try:
        configured = sources("configs/sources.json", enabled_only=True)
        automated = [
            item for item in configured
            if item["acquisition_mode"] != "manual_discovery"
        ]
    except RegistryError:
        automated = [{"id": provider, "acquisition_mode": "existing_provider"} for provider in REQUIRED_PROVIDERS]
    paths = [
        f"data/{item['id']}/processed/{name}"
        for item in automated for name in COMMON_OUTPUTS
    ]
    paths += [
        f"data/{item['id']}/processed/acquisition.json"
        for item in automated if item["acquisition_mode"] != "existing_provider"
    ]
    paths += ["data/source_status.json"]
    paths += ["data/neura/processed/jobs_structured.csv", "data/spacex/processed/acquisition.json"]
    paths += [f"data/spacex/processed/{name}" for name in PUBLIC_FEED_FILES]
    paths += [f"data/patrick/processed/{name}" for name in PUBLIC_FEED_FILES]
    return tuple(dict.fromkeys(paths))


OUTPUT_ALLOWLIST = output_allowlist()


class PublicationError(RuntimeError):
    pass


def run(command, check=True):
    print("+ " + " ".join(command), flush=True)
    result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n", flush=True)
    if check and result.returncode:
        raise PublicationError(f"Command failed ({result.returncode}): {' '.join(command)}")
    return result


def read_csv(path, required):
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            fields = set(reader.fieldnames or ())
            if not required.issubset(fields):
                raise PublicationError(f"{path} is missing fields: {', '.join(sorted(required - fields))}")
            rows = list(reader)
    except OSError as exc:
        raise PublicationError(f"Cannot read required output {path}: {exc}") from exc
    if not rows:
        raise PublicationError(f"Required output is empty: {path}")
    return rows


def validate_datasets(repo, collection_started):
    counts = {}
    for provider in REQUIRED_PROVIDERS:
        processed = repo / "data" / provider / "processed"
        latest_path = processed / "jobs_latest.csv"
        try:
            fresh = latest_path.stat().st_mtime >= collection_started
        except OSError as exc:
            raise PublicationError(f"Missing current {provider} collection: {latest_path}") from exc
        if not fresh:
            raise PublicationError(f"Stale {provider} collection: jobs_latest.csv was not refreshed")
        jobs = read_csv(latest_path, JOB_FIELDS)
        details = read_csv(processed / "job_details.csv", DETAIL_FIELDS)
        job_links = {row["link"].strip() for row in jobs if row.get("link", "").strip()}
        detail_links = {row["link"].strip() for row in details if row.get("link", "").strip()}
        missing = job_links - detail_links
        if missing:
            raise PublicationError(f"{provider} details are incoherent: {len(missing)} current jobs lack details")
        for name in COMMON_OUTPUTS:
            path = processed / name
            if not path.is_file() or path.stat().st_size == 0:
                raise PublicationError(f"Required processed output is missing or empty: {path}")
        counts[provider] = len(jobs)

    acquisition_path = repo / "data/spacex/processed/acquisition.json"
    try:
        acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
        observed = datetime.fromisoformat(acquisition["observed_at"].replace("Z", "+00:00")).timestamp()
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise PublicationError(f"Invalid SpaceX acquisition metadata: {exc}") from exc
    if acquisition.get("coverage_complete") is not True or acquisition.get("records_written") != counts["spacex"]:
        raise PublicationError("SpaceX acquisition metadata does not match the processed dataset")
    if observed < collection_started:
        raise PublicationError("SpaceX acquisition metadata is stale")
    return counts


def publish_patrick_feed(repo, runtime, profile, counts):
    output = runtime / "patrick-feed"
    run([
        sys.executable, "analysis/profile_ranking.py", "spacex",
        "--profile", str(profile), "--data-dir", "data/spacex",
        "--output-dir", str(output), "--require-profile",
    ])
    try:
        document = json.loads((output / "spacex_targets.json").read_text(encoding="utf-8"))
        with (output / "spacex_targets.csv").open(newline="", encoding="utf-8-sig") as handle:
            feed_rows = list(csv.DictReader(handle))
        markdown = (output / "spacex_targets.md").read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicationError(f"Patrick feed validation failed: {exc}") from exc
    rankings = document.get("rankings")
    metadata = document.get("metadata", {})
    if not isinstance(rankings, list) or len(rankings) != len(feed_rows) or len(rankings) != counts["spacex"]:
        raise PublicationError("Patrick JSON, CSV, and SpaceX dataset counts are incoherent")
    if metadata.get("coverage_complete") is not True or not markdown.startswith("# SpaceX targets"):
        raise PublicationError("Patrick feed schema or coverage marker is invalid")

    destination = repo / "data/spacex/processed"
    source_names = ("spacex_targets.csv", "spacex_targets.json", "spacex_targets.md")
    for source_name, destination_name in zip(source_names, PUBLIC_FEED_FILES):
        source = output / source_name
        handle = tempfile.NamedTemporaryFile(dir=destination, prefix=".patrick.", delete=False)
        temporary = Path(handle.name)
        try:
            with handle, source.open("rb") as input_handle:
                shutil.copyfileobj(input_handle, handle)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, destination / destination_name)
        finally:
            temporary.unlink(missing_ok=True)
    space_sources = [
        item for item in sources(repo / "configs/sources.json", enabled_only=True)
        if item["sector"] == "Space/Rocket"
        and "patrick" in item["tags"]
        and item["acquisition_mode"] != "manual_discovery"
    ]
    multi = generate_multi(
        profile, space_sources, repo / "data", repo / "data/patrick/processed"
    )
    if not multi["metadata"]["coverage_complete"]:
        incomplete = [
            item["source_id"] for item in multi["metadata"]["source_coverage"]
            if not item["coverage_complete"]
        ]
        raise PublicationError("Patrick feed has incomplete source coverage: " + ", ".join(incomplete))
    return len(multi["rankings"])


def changed_paths():
    result = run(["git", "status", "--porcelain=v1", "--untracked-files=all"])
    paths = set()
    for line in result.stdout.splitlines():
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.add(path.strip('"'))
    return paths


def require_clean_git():
    dirty = changed_paths()
    if dirty:
        raise PublicationError("Refusing to collect with existing worktree changes: " + ", ".join(sorted(dirty)))


def require_tracked_allowlist():
    result = run(["git", "ls-files", "--error-unmatch", "--", *OUTPUT_ALLOWLIST], check=False)
    if result.returncode:
        raise PublicationError(
            "Every public output must be reviewed and tracked before unattended publication; "
            "the output allowlist contains an untracked path"
        )


def validate_enabled_providers(repo):
    try:
        registry_path = repo / "configs/sources.json"
        if registry_path.exists():
            enabled = {item["id"] for item in sources(registry_path, enabled_only=True)}
        else:
            config = json.loads((repo / "configs/companies.json").read_text(encoding="utf-8"))
            enabled = {item.get("name") for item in config if item.get("enabled") is True}
    except (OSError, json.JSONDecodeError, RegistryError) as exc:
        raise PublicationError(f"Cannot load source registry: {exc}") from exc
    missing = set(REQUIRED_PROVIDERS) - enabled
    if missing:
        raise PublicationError("Required providers are disabled: " + ", ".join(sorted(missing)))


def git_prepare(expected_branch):
    branch = run(["git", "branch", "--show-current"]).stdout.strip()
    if branch != expected_branch:
        raise PublicationError(f"Expected publication branch {expected_branch!r}, found {branch!r}")
    require_clean_git()
    run(["git", "fetch", "origin", "main"])
    relation = run(["git", "rev-list", "--left-right", "--count", "HEAD...origin/main"]).stdout.split()
    if len(relation) != 2:
        raise PublicationError("Cannot determine relationship to origin/main")
    ahead, behind = map(int, relation)
    if ahead and behind:
        raise PublicationError("Local publication history diverges from origin/main; refusing to reset or merge")
    run(["git", "pull", "--ff-only", "origin", "main"])


def commit_and_push(counts, feed_count, publish_ref):
    dirty = changed_paths()
    unexpected = dirty - set(OUTPUT_ALLOWLIST)
    if unexpected:
        raise PublicationError("Collection changed files outside the public output allowlist: " + ", ".join(sorted(unexpected)))
    run(["git", "add", "--", *OUTPUT_ALLOWLIST])
    if run(["git", "diff", "--cached", "--quiet"], check=False).returncode == 0:
        print("No public dataset or feed changes; no commit created.")
        return False
    summary = " ".join(f"{provider}={counts[provider]}" for provider in REQUIRED_PROVIDERS)
    run(["git", "commit", "-m", f"Publish datasets ({summary}; patrick={feed_count})"])
    try:
        run(["git", "push", "origin", f"HEAD:{publish_ref}"])
    except PublicationError as exc:
        sha = run(["git", "rev-parse", "HEAD"]).stdout.strip()
        raise PublicationError(
            f"Push failed; local output commit {sha} was preserved. Resolve remote access/history, then rerun "
            f"`git push origin HEAD:{publish_ref}` without force."
        ) from exc
    return True


def collect_and_publish(repo, runtime, profile, expected_branch, publish_ref):
    git_prepare(expected_branch)
    require_tracked_allowlist()
    validate_enabled_providers(repo)
    collection_started = time.time()
    command = [sys.executable, "run_pipeline.py"]
    for provider in REQUIRED_PROVIDERS:
        command.extend(("--company", provider))
    run(command)
    registry_sources = [
        item for item in sources(repo / "configs/sources.json", enabled_only=True)
        if item["acquisition_mode"] not in {"existing_provider", "manual_discovery"}
    ]
    if registry_sources:
        registry_command = [sys.executable, "-m", "jobtracker.pipeline"]
        for item in registry_sources:
            registry_command.extend(("--source", item["id"]))
        run(registry_command)
    counts = validate_datasets(repo, collection_started)
    feed_count = publish_patrick_feed(repo, runtime, profile, counts)
    committed = commit_and_push(counts, feed_count, publish_ref)
    action = "committed and pushed" if committed else "validated with no public changes"
    print(f"Publication {action}: " + " ".join(f"{key}={value}" for key, value in counts.items()))
    return committed


def main():
    repo = Path(__file__).resolve().parents[1]
    os.chdir(repo)
    runtime = Path(os.environ.get("JOB_TRACKER_RUNTIME_DIR", ".runtime/publication")).resolve()
    runtime.mkdir(parents=True, exist_ok=True)
    profile = Path(os.environ.get("JOB_TRACKER_PROFILE_PATH", "configs/private_profiles/patrick.json")).resolve()
    expected_branch = os.environ.get("JOB_TRACKER_PUBLISH_BRANCH", "main")
    publish_ref = os.environ.get("JOB_TRACKER_PUBLISH_REF", "main")
    lock_path = runtime / "publication.lock"
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise PublicationError(f"Another publication run holds {lock_path}") from exc
        collect_and_publish(repo, runtime, profile, expected_branch, publish_ref)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PublicationError as exc:
        print(f"PUBLICATION FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
