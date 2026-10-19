#!/usr/bin/env python3
"""Persist and enforce the Hostinger publisher's rolling 48-hour eligibility."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

MINIMUM_INTERVAL = timedelta(hours=48)
RETRY_INTERVAL = timedelta(hours=6)
STATE_VERSION = 1


class SchedulerStateError(RuntimeError):
    pass


def parse_utc(value: str) -> datetime:
    if not isinstance(value, str):
        raise SchedulerStateError("Timestamp must be a string in ISO-8601 UTC format")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SchedulerStateError(f"Invalid timestamp {value!r}; expected an ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise SchedulerStateError(f"Timestamp must include UTC timezone: {value!r}")
    return parsed.astimezone(timezone.utc)


def format_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() != timedelta(0):
        raise SchedulerStateError("Internal timestamp is not timezone-aware UTC")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


def read_state(path: Path) -> dict:
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SchedulerStateError(
            f"Scheduler state is missing: {path}; initialize it from verified journal evidence"
        ) from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise SchedulerStateError(f"Cannot read scheduler state {path}: {exc}") from exc

    if not isinstance(state, dict) or state.get("version") != STATE_VERSION:
        raise SchedulerStateError(f"Unsupported or malformed scheduler state in {path}")
    last_success = state.get("last_success_utc")
    first_run_after = state.get("first_run_after_utc")
    last_attempt = state.get("last_attempt_utc")
    attempt_invocation_id = state.get("last_attempt_invocation_id")
    attempt_status = state.get("last_attempt_status")
    last_failure = state.get("last_failure_utc")
    if last_success is not None and first_run_after is not None:
        raise SchedulerStateError(f"Scheduler state has conflicting eligibility anchors: {path}")
    if last_success is None and first_run_after is None:
        raise SchedulerStateError(f"Scheduler state has no eligibility anchor: {path}")
    if last_success is not None:
        parse_utc(last_success)
    if first_run_after is not None:
        parse_utc(first_run_after)
    if not (
        (isinstance(last_success, str) and first_run_after is None)
        or (last_success is None and isinstance(first_run_after, str))
    ):
        raise SchedulerStateError(f"Malformed eligibility anchor in {path}")
    if last_attempt is not None:
        parse_utc(last_attempt)
    if last_failure is not None:
        parse_utc(last_failure)
    if not (
        (
            last_attempt is None
            and attempt_invocation_id is None
            and attempt_status is None
            and last_failure is None
        )
        or (
            isinstance(last_attempt, str)
            and isinstance(attempt_invocation_id, str)
            and attempt_status in {"started", "success", "failed"}
            and (attempt_status != "failed" or isinstance(last_failure, str))
            and (attempt_status != "success" or isinstance(last_success, str))
        )
    ):
        raise SchedulerStateError(f"Malformed attempt/failure state in {path}")
    return state


def write_state(path: Path, state: dict) -> None:
    if not path.parent.is_dir():
        raise SchedulerStateError(f"Scheduler state directory does not exist: {path.parent}")
    temporary_path = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", dir=path.parent, text=True
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(state, handle, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, 0o644)
        os.replace(temporary_path, path)
        if os.name == "posix":
            directory_fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    except OSError as exc:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise SchedulerStateError(f"Cannot atomically write scheduler state {path}: {exc}") from exc


def initialize_state(
    path: Path,
    *,
    last_success_utc: str | None = None,
    first_run_after_utc: str | None = None,
) -> None:
    if (last_success_utc is None) == (first_run_after_utc is None):
        raise SchedulerStateError(
            "Provide exactly one of --last-success-utc or --first-run-after-utc"
        )
    if path.exists():
        raise SchedulerStateError(f"Refusing to overwrite existing scheduler state: {path}")
    state = {
        "version": STATE_VERSION,
        "last_success_utc": (
            format_utc(parse_utc(last_success_utc)) if last_success_utc is not None else None
        ),
        "first_run_after_utc": (
            format_utc(parse_utc(first_run_after_utc))
            if first_run_after_utc is not None else None
        ),
        "last_attempt_utc": None,
        "last_attempt_invocation_id": None,
        "last_attempt_status": None,
        "last_failure_utc": None,
    }
    write_state(path, state)


def eligibility_deadline(path: Path) -> datetime:
    state = read_state(path)
    if state["last_success_utc"] is not None:
        return parse_utc(state["last_success_utc"]) + MINIMUM_INTERVAL
    return parse_utc(state["first_run_after_utc"])


def is_eligible(path: Path, now: datetime | None = None) -> bool:
    return (now or datetime.now(timezone.utc)) >= next_attempt_after(path)


def next_attempt_after(path: Path) -> datetime:
    state = read_state(path)
    deadline = eligibility_deadline(path)
    if state["last_attempt_status"] == "started":
        deadline = max(
            deadline,
            parse_utc(state["last_attempt_utc"]) + RETRY_INTERVAL,
        )
    elif state["last_attempt_status"] == "failed":
        deadline = max(
            deadline,
            parse_utc(state["last_failure_utc"]) + RETRY_INTERVAL,
        )
    return deadline


def mark_attempt(
    path: Path,
    invocation_id: str,
    now: datetime | None = None,
) -> str:
    if not invocation_id:
        raise SchedulerStateError("systemd INVOCATION_ID is required to record an attempt")
    state = read_state(path)
    timestamp = format_utc(now or datetime.now(timezone.utc))
    state["last_attempt_utc"] = timestamp
    state["last_attempt_invocation_id"] = invocation_id
    state["last_attempt_status"] = "started"
    write_state(path, state)
    return timestamp


def record_success(
    path: Path,
    invocation_id: str,
    now: datetime | None = None,
) -> str:
    state = read_state(path)
    if (
        state["last_attempt_status"] != "started"
        or state["last_attempt_invocation_id"] != invocation_id
    ):
        raise SchedulerStateError("Cannot record success without a persisted publisher attempt")
    timestamp = format_utc(now or datetime.now(timezone.utc))
    state["last_success_utc"] = timestamp
    state["first_run_after_utc"] = None
    state["last_attempt_status"] = "success"
    write_state(path, state)
    return timestamp


def record_failure(
    path: Path,
    service_result: str,
    invocation_id: str,
    now: datetime | None = None,
) -> str | None:
    if service_result == "success":
        return None
    if not invocation_id:
        raise SchedulerStateError("systemd INVOCATION_ID is required to record a failure")
    state = read_state(path)
    if (
        state["last_attempt_status"] != "started"
        or state["last_attempt_invocation_id"] != invocation_id
    ):
        return None
    timestamp = format_utc(now or datetime.now(timezone.utc))
    state["last_failure_utc"] = timestamp
    state["last_attempt_status"] = "failed"
    write_state(path, state)
    return timestamp


def run_command(args: argparse.Namespace) -> int:
    if args.command == "initialize":
        initialize_state(
            args.state_file,
            last_success_utc=args.last_success_utc,
            first_run_after_utc=args.first_run_after_utc,
        )
        print(f"[OK] Initialized scheduler state: {args.state_file}")
        return 0
    if args.command == "record-success":
        timestamp = record_success(args.state_file, args.invocation_id)
        print(f"[OK] Recorded successful publisher execution at {timestamp}")
        return 0
    if args.command == "record-outcome":
        timestamp = record_failure(
            args.state_file,
            args.service_result,
            args.invocation_id,
        )
        if timestamp is None:
            print(f"[INFO] No failed publisher attempt to record (service result: {args.service_result})")
        else:
            print(f"[WARN] Recorded failed publisher attempt at {timestamp}")
        return 0

    now = datetime.now(timezone.utc)
    deadline = next_attempt_after(args.state_file)
    if now < deadline:
        print(f"[WAIT] Publisher not eligible before {format_utc(deadline)}")
        return 1
    invocation_id = os.environ.get("INVOCATION_ID")
    if not invocation_id:
        raise SchedulerStateError("systemd INVOCATION_ID is unavailable; refusing to run publisher")
    timestamp = mark_attempt(args.state_file, invocation_id, now)
    print(f"[OK] Publisher is eligible; recorded attempt at {timestamp}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    initialize = subparsers.add_parser("initialize")
    initialize.add_argument("--state-file", required=True, type=Path)
    anchor = initialize.add_mutually_exclusive_group(required=True)
    anchor.add_argument("--last-success-utc")
    anchor.add_argument("--first-run-after-utc")
    for command in ("eligible", "record-success"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--state-file", required=True, type=Path)
        if command == "record-success":
            subparser.add_argument("--invocation-id", required=True)
    record_outcome = subparsers.add_parser("record-outcome")
    record_outcome.add_argument("--state-file", required=True, type=Path)
    record_outcome.add_argument("--service-result", required=True)
    record_outcome.add_argument("--invocation-id", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return run_command(args)
    except SchedulerStateError as exc:
        print(f"[ERR] {exc}", file=sys.stderr)
        return 255


if __name__ == "__main__":
    raise SystemExit(main())
