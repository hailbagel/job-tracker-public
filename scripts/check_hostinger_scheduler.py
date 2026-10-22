#!/usr/bin/env python3
"""Read-only Hostinger scheduler status and last-success freshness check."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.hostinger_scheduler_state import (
    MINIMUM_INTERVAL,
    SchedulerStateError,
    parse_utc,
    read_state,
)

DEFAULT_STATE_FILE = Path("/var/lib/vutrulabs-job-tracker-public/state.json")
# A healthy scheduler may have one active cadence interval in flight. A
# success becomes stale only after it misses the following interval too.
STALE_AFTER = MINIMUM_INTERVAL * 2


def systemd_properties(unit: str, properties: tuple[str, ...]) -> str:
    command = [
        "systemctl", "show", unit,
        *(f"--property={property_name}" for property_name in properties),
        "--no-pager",
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode:
        details = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"systemctl show failed for {unit}: {details}")
    return result.stdout.rstrip()


def format_age(age: timedelta) -> str:
    seconds = int(age.total_seconds())
    return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


def run_check(state_file: Path, now: datetime | None = None) -> int:
    timer_properties = (
        "ActiveState", "SubState", "LastTriggerUSec",
        "NextElapseUSecRealtime", "NextElapseUSecMonotonic", "Persistent",
    )
    service_properties = (
        "ActiveState", "SubState", "Result", "ExecMainStatus",
        "ExecMainStartTimestamp", "ExecMainExitTimestamp",
    )
    print("[INFO] Timer state")
    print(systemd_properties("vutrulabs-job-tracker-public.timer", timer_properties))
    print("[INFO] Publisher service state")
    print(systemd_properties("vutrulabs-job-tracker-public.service", service_properties))

    state = read_state(state_file)
    last_success = state["last_success_utc"]
    if last_success is None:
        eligible_after = parse_utc(state["first_run_after_utc"])
        print(f"[WARN] No successful publisher execution recorded yet; first run not before {eligible_after.isoformat()}")
        if state["last_attempt_utc"] is not None:
            print(
                f"[INFO] Last publisher attempt: {state['last_attempt_utc']} "
                f"({state['last_attempt_status']})"
            )
        if state["last_failure_utc"] is not None:
            print(f"[WARN] Last failed publisher attempt: {state['last_failure_utc']}")
        return 1

    current_time = now or datetime.now(timezone.utc)
    age = current_time - parse_utc(last_success)
    if age < timedelta(0):
        print(f"[ERR] Host clock precedes the recorded publisher success: {last_success}")
        return 2
    print(f"[INFO] Last successful publisher execution: {last_success}")
    print(f"[INFO] Publisher success age: {format_age(age)}")
    if state["last_attempt_utc"] is not None:
        print(
            f"[INFO] Last publisher attempt: {state['last_attempt_utc']} "
            f"({state['last_attempt_status']})"
        )
    if state["last_failure_utc"] is not None:
        print(f"[WARN] Last failed publisher attempt: {state['last_failure_utc']}")
    stale_after = format_age(STALE_AFTER)
    if age > STALE_AFTER:
        print(f"[ERR] Last successful publisher execution is stale (>{stale_after})")
        return 1
    print(f"[OK] Last successful publisher execution is within {stale_after}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE)
    args = parser.parse_args()
    try:
        return run_check(args.state_file)
    except (OSError, RuntimeError, SchedulerStateError) as exc:
        print(f"[ERR] Scheduler smoke-test failed: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
