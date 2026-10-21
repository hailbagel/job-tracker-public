# Hostinger SMS group production pilot and rollback runbook

Status: preparation only. This document does not authorize production activation. Run the commands below only in the Hostinger Web Terminal, as root, after the owner approves the pilot window and the complete pre-flight passes. No Hostinger command was run while preparing this document.

## Verified code and deployment contract

- PR [#25](https://github.com/hailbagel/job-tracker-public/pull/25) is merged into `main` as `daa9a086c9fadda413d38bb66d5168d1c34f98bd`. The Industrial source Linux CI and Hostinger scheduler/publisher Linux review both passed.
- `configs/sources.json` configures the enabled `sms-group` source with the `dvinci` adapter, official feed and sitemap URLs, and `production_opt_in_env: JOB_TRACKER_ENABLE_SMS_GROUP`.
- `jobtracker/acquisition.py` requires the environment value to equal exactly `1`; absent, empty, and other values do not enable collection. The adapter checks that feed and sitemap use the official careers host, validates the feed publication identities and canonical URLs, and requires the sitemap publication-ID set to equal the feed publication-ID set. It selects one language variant per opening, preferring English. This supports feed/sitemap ID equivalence, not a claim that every sitemap URL is a unique job opening or that every live detail page was independently verified.
- `scripts/publish_public_data.py` includes SMS normalized files in the reviewed output allowlist, leaves the bootstrap untouched while opt-in is off, validates fresh nonempty job/detail data and complete acquisition metadata before publishing, and restores tracked last-good source datasets if collection fails. SMS is not a Space/Rocket Patrick contributor.
- `scripts/audit_public_data.py` is read-only. It checks metadata, source datasets, history, summaries, feed parity, and the exact tracked data-path set.
- `scripts/hostinger_scheduler_state.py` supplies the durable eligibility gate. The repository has a tracked `20-scheduler-gate.conf` contract and an hourly timer check; the state gate enforces the six-hour minimum interval and six-hour failed-attempt backoff. The actual Hostinger unit and timer have not been verified for this runbook: the pre-flight must confirm the installed contract matches the approved state gate before any activation. Preserve the timer, state file, publisher lock, and existing unit/drop-ins.
- `tests/test_publication.py` and `tests/test_public_data_audit.py` cover disabled-by-default behavior, bootstrap replacement, failure restoration, status metadata, and audit consistency.
- The tracked SMS bootstrap is intentionally empty: all six processed CSVs contain headers only; acquisition and source status say `incomplete`, `records_written: 0`, `coverage_complete: false`, and `awaiting_first_verified_production_run`.

## Important owner warnings

- PR #25 is code and bootstrap only. It did not activate SMS on Hostinger.
- GitHub Actions success is not live Hostinger verification.
- `JOB_TRACKER_ENABLE_SMS_GROUP` must remain unset until the approved pilot activation.
- No additional full production run has been verified after the PR #25 merge.
- Never describe SMS as live until the published acquisition metadata and full audit prove a successful production collection.
- Do not add SMS to Space/Rocket or Patrick rankings; do not change the registry sector or tags to achieve that.
- Do not bypass the existing publisher, timer, eligibility gate, six-hour error backoff, or publication lock. Do not run a scraper directly.

## 1. Read-only Hostinger pre-flight

Copy this entire block into a normal Hostinger Web Terminal root shell. It makes no repository, unit, state, or data changes. It prints scheduler metadata and public job counts only. Systemd output redacts environment values, environment-file paths, and private-profile arguments. The unit checker reads relevant environment-file lines but never prints their contents.

```bash
set -euo pipefail
REPO=/opt/vutrulabs/job-tracker-public
SERVICE=vutrulabs-job-tracker-public.service
TIMER=vutrulabs-job-tracker-public.timer
STATE=/var/lib/vutrulabs-job-tracker-public/state.json
MERGE=daa9a086c9fadda413d38bb66d5168d1c34f98bd
SMS=JOB_TRACKER_ENABLE_SMS_GROUP

test "$(id -u)" -eq 0 || { echo '[ERR] Open a root shell.'; exit 1; }
cd "$REPO"
test "$(pwd -P)" = "$REPO" || { echo '[ERR] Repository path mismatch.'; exit 1; }
printf '%s\n' '=== HOST AND REPOSITORY ==='
id -un
printf 'repo=%s\n' "$(pwd -P)"
printf 'branch=%s\n' "$(git branch --show-current)"
printf 'head=%s\n' "$(git rev-parse HEAD)"
test "$(git branch --show-current)" = main || {
    echo '[ERR] Host checkout is not on main.'
    exit 1
}
test -z "$(git status --porcelain=v1 --untracked-files=all)" || {
    echo '[ERR] Host worktree is not clean; do not proceed.'
    git status --short --branch
    exit 1
}
git merge-base --is-ancestor "$MERGE" HEAD || {
    echo '[ERR] Host main does not contain the PR #25 merge.'
    exit 1
}
echo '[OK] Clean main contains the PR #25 merge.'

printf '%s\n' '=== GITHUB MAIN REF (READ ONLY) ==='
git ls-remote --exit-code origin refs/heads/main

printf '%s\n' '=== SYSTEMD UNIT AND DROP-INS (VALUES REDACTED) ==='
systemctl cat "$SERVICE" "$TIMER" | python3 -c '
import re, sys
for line in sys.stdin:
    if re.match(r"^\s*Environment=", line):
        print(re.sub(r"^(\s*Environment)=.*$", r"\1=[values redacted]", line.rstrip()))
    elif re.match(r"^\s*EnvironmentFile=", line):
        print(re.sub(r"^(\s*EnvironmentFile)=.*$", r"\1=[path redacted]", line.rstrip()))
    else:
        line = re.sub(r"(--profile(?:=|\s+))[^ ;}]+", r"\1[REDACTED]", line.rstrip())
        line = re.sub(
            r"(--(?:token|password|secret|credential|cookie|api[-_]?key)(?:=|\s+))[^ ;}]+",
            r"\1[REDACTED]", line, flags=re.IGNORECASE,
        )
        line = re.sub(r"(https?://)[^/@\s]+:[^/@\s]+@", r"\1[REDACTED]@", line, flags=re.IGNORECASE)
        line = re.sub(r"/[^ ;}]*private_profiles/[^ ;}]+", "[PRIVATE_PROFILE_PATH]", line)
        print(line)
'
systemctl show "$SERVICE" --no-pager \
    -p FragmentPath -p DropInPaths -p Type -p Restart -p User -p Group \
    -p WorkingDirectory -p ExecStart -p StateDirectory -p StateDirectoryMode \
    -p EnvironmentFiles -p PassEnvironment -p ExecCondition -p ExecStopPost \
    -p ActiveState -p SubState -p Result -p ExecMainStatus | sed -E \
    -e 's#(EnvironmentFiles=).*#\1[paths redacted]#' \
    -e 's#(--profile(=| )[^ ;}]+)#--profile [REDACTED]#g' \
    -e 's#(--(token|password|secret|credential|cookie|api[-_]?key)(=| )[^ ;}]+)#\1[REDACTED]#Ig' \
    -e 's#(https?://)[^/@ ]+:[^/@ ]+@#\1[REDACTED]@#Ig' \
    -e 's#/[^ ;}]*private_profiles/[^ ;}]+#[PRIVATE_PROFILE_PATH]#g'
systemctl show "$TIMER" --no-pager \
    -p FragmentPath -p DropInPaths -p Unit -p ActiveState -p SubState \
    -p LastTriggerUSec -p NextElapseUSecRealtime
printf '%s\n' '=== TIMER ENABLEMENT AND NEXT TICK ==='
systemctl is-enabled "$TIMER"
systemctl is-active "$TIMER"
systemctl list-timers --all "$TIMER" --no-pager
systemctl is-active --quiet "$SERVICE" && {
    echo '[ERR] Publisher service is active; do not proceed.'
    exit 1
}
pgrep -f '[s]cripts/publish_public_data\.py' >/dev/null && {
    echo '[ERR] A publisher process is active; do not proceed.'
    exit 1
}
printf '%s\n' '=== CLOCK ==='
NTP_SYNC=$(timedatectl show -p NTPSynchronized --value)
printf 'NTPSynchronized=%s\n' "$NTP_SYNC"
test "$NTP_SYNC" = yes || { echo '[ERR] Host time synchronization is not confirmed.'; exit 1; }

printf '%s\n' '=== OPT-IN ABSENCE ==='
python3 - "$SERVICE" "$SMS" <<'PY'
import os
import re
import shlex
import subprocess
import sys

unit, sms = sys.argv[1:]
text = subprocess.check_output(["systemctl", "cat", unit], text=True)
for line in text.splitlines():
    stripped = line.strip()
    if stripped.startswith("Environment="):
        tokens = shlex.split(stripped.split("=", 1)[1])
        if any(token.split("=", 1)[0] == sms for token in tokens):
            raise SystemExit("[ERR] SMS opt-in is explicitly assigned in a unit/drop-in.")
    if stripped.startswith("EnvironmentFile="):
        for path in shlex.split(stripped.split("=", 1)[1]):
            optional = path.startswith("-")
            path = path[1:] if optional else path
            if not os.path.isfile(path):
                if optional:
                    continue
                raise SystemExit("[ERR] A required EnvironmentFile is missing.")
            with open(path, encoding="utf-8", errors="replace") as handle:
                if any(re.match(r"^\s*" + re.escape(sms) + r"\s*=", item) for item in handle):
                    raise SystemExit("[ERR] SMS opt-in is assigned in an EnvironmentFile.")
passed = subprocess.check_output(
    ["systemctl", "show", "-p", "PassEnvironment", "--value", unit], text=True
).split()
if sms in passed or "*" in passed:
    raise SystemExit("[ERR] PassEnvironment could import an unverified SMS opt-in.")
print("[OK] SMS opt-in is not assigned in the unit, drop-ins, or EnvironmentFiles.")
print("[OK] No PassEnvironment setting can import an unverified SMS opt-in.")
PY

printf '%s\n' '=== SCHEDULER STATE (READ ONLY) ==='
test -r "$STATE" || { echo '[ERR] Installed scheduler state is missing/unreadable.'; exit 1; }
stat -c 'state_file=%n mode=%a owner=%U:%G' "$STATE"
test "$(stat -c '%U:%a' "$STATE")" = 'root:600' || {
    echo '[ERR] Scheduler state must be root-owned with mode 600.'
    exit 1
}
test "$(stat -c '%a' "$(dirname "$STATE")")" = 700 || {
    echo '[ERR] Scheduler state directory must have mode 700.'
    exit 1
}
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 - "$REPO" "$STATE" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts import hostinger_scheduler_state as scheduler
path = Path(sys.argv[2])
state = scheduler.read_state(path)
for key in (
    "version", "last_success_utc", "first_run_after_utc",
    "last_attempt_utc", "last_attempt_status", "last_failure_utc",
):
    print(f"{key}={state[key]}")
print("eligibility_deadline_utc=" + scheduler.format_utc(scheduler.eligibility_deadline(path)))
print("next_attempt_after_utc=" + scheduler.format_utc(scheduler.next_attempt_after(path)))
PY
set +e
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 \
    "$REPO/scripts/hostinger_scheduler_state.py" eligible \
    --state-file "$STATE" --dry-run
ELIGIBILITY_RC=$?
set -e
case "$ELIGIBILITY_RC" in
    0) echo '[OK] Scheduler state currently permits an eligible invocation.' ;;
    1) echo '[INFO] Not yet eligible; leave the existing timer to check at its next tick.' ;;
    *) echo '[ERR] Scheduler state check failed.'; exit "$ELIGIBILITY_RC" ;;
esac

printf '%s\n' '=== SMS REGISTRY, GATE, AND BOOTSTRAP ==='
PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 - "$REPO" <<'PY'
import csv
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root))
from jobtracker.acquisition import source_opt_in_enabled
from jobtracker.processing import (
    CHANGE_FIELDS, DETAIL_FIELDS, LATEST_FIELDS,
)
from jobtracker.registry import sources

source = next(item for item in sources(root / "configs/sources.json") if item["id"] == "sms-group")
assert source["production_opt_in_env"] == "JOB_TRACKER_ENABLE_SMS_GROUP"
assert source["sector"] != "Space/Rocket" and "patrick" not in source["tags"]
assert source_opt_in_enabled(source, {}) is False
assert source_opt_in_enabled(source, {"JOB_TRACKER_ENABLE_SMS_GROUP": "0"}) is False
assert source_opt_in_enabled(source, {"JOB_TRACKER_ENABLE_SMS_GROUP": "1"}) is True
print("registry=enabled api/dvinci; sector and tags exclude Space/Rocket and Patrick")
print("empty_or_zero_opt_in=disabled; exact_1_opt_in=enabled")

processed = root / "data/sms-group/processed"
expected = {
    "jobs_latest.csv": tuple(LATEST_FIELDS),
    "job_details.csv": tuple(DETAIL_FIELDS),
    "job_history.csv": tuple(DETAIL_FIELDS) + ("first_seen", "last_seen", "active"),
    "job_changes.csv": tuple(CHANGE_FIELDS),
    "department_summary.csv": ("department", "count"),
    "location_summary.csv": ("location", "count"),
}
for name, fields in expected.items():
    with (processed / name).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        assert tuple(reader.fieldnames or ()) == fields, f"{name}: unexpected header"
        assert next(reader, None) is None, f"{name}: bootstrap contains rows"
    print(f"bootstrap={name}: reviewed header only")

acquisition = json.loads((processed / "acquisition.json").read_text(encoding="utf-8"))
assert acquisition["status"] == "incomplete"
assert acquisition["coverage_complete"] is False
assert acquisition["records_written"] == 0
assert acquisition["publication_status"] == "awaiting_first_verified_production_run"
status = json.loads((root / "data/source_status.json").read_text(encoding="utf-8"))
sms = next(item for item in status["sources"] if item["source_id"] == "sms-group")
assert sms["attempted"] is False and sms["status"] == "incomplete"
assert sms["coverage_complete"] is False and sms["records_written"] == 0
assert sms["publication_status"] == "awaiting_first_verified_production_run"
assert "sms-group" not in status["publication"]["attempted_sources"]
assert "sms-group" in status["publication"]["failed_or_incomplete_sources"]
print("acquisition and source_status metadata=disabled bootstrap, incomplete, zero, unattempted")
PY
git ls-files --error-unmatch \
    data/sms-group/processed/acquisition.json \
    data/sms-group/processed/department_summary.csv \
    data/sms-group/processed/job_changes.csv \
    data/sms-group/processed/job_details.csv \
    data/sms-group/processed/job_history.csv \
    data/sms-group/processed/jobs_latest.csv \
    data/sms-group/processed/location_summary.csv
git ls-files --error-unmatch scripts/hostinger_scheduler_state.py \
    scripts/publish_public_data.py scripts/audit_public_data.py \
    scripts/systemd/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf \
    scripts/systemd/vutrulabs-job-tracker-public.timer

printf '%s\n' '=== LAST SUCCESSFUL PUBLICATION EVIDENCE ==='
LAST_PUBLISH=$(git log -1 --format='%h %cI %s' --grep='Publish datasets')
test -n "$LAST_PUBLISH" || { echo '[ERR] No publisher commit is present in local Git history.'; exit 1; }
printf '%s\n' "$LAST_PUBLISH"
printf 'scheduler_state_last_success_utc='
/usr/bin/python3 - "$REPO" "$STATE" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts.hostinger_scheduler_state import read_state
print(read_state(Path(sys.argv[2]))["last_success_utc"])
PY

printf '%s\n' '=== PYTHON TEST READINESS ==='
test -x "$REPO/.venv/bin/python" || {
    echo '[ERR] Expected service virtualenv Python is missing; inspect actual ExecStart before proceeding.'
    exit 1
}
PYTHONDONTWRITEBYTECODE=1 "$REPO/.venv/bin/python" --version
PYTHONDONTWRITEBYTECODE=1 "$REPO/.venv/bin/python" -m unittest --help >/dev/null
test -f tests/test_publication.py
test -f tests/test_public_data_audit.py
echo '[OK] Python unittest runner and PR #25 test modules are present.'

printf '%s\n' '=== READ-ONLY FULL DATA AUDIT ==='
PYTHONDONTWRITEBYTECODE=1 "$REPO/.venv/bin/python" scripts/audit_public_data.py
```

### Pre-flight decision gate

Stop without changing anything if the host path, `main` checkout, clean worktree, merge ancestry, timer, service contract, scheduler state, opt-in status, or bootstrap assertions fail or are ambiguous. Review the complete effective `ExecStart`, working directory, root/service identity, `StateDirectory`, `ExecCondition`, `ExecStopPost`, `PassEnvironment`, `EnvironmentFiles`, and drop-in list privately. The existing service must still invoke the approved public publisher; do not replace its command or alter any unrelated drop-in.

The current checked-in data audit baseline is **0 FAIL / 3 WARN**: Tesla's preserved stale data, Jacobs' preserved stale data, and the deliberately empty SMS bootstrap. For SMS, the audit's generic `failed collection` warning describes the unattempted/incomplete bootstrap; it does not mean collection was attempted. The audit can also warn about unknown locations or details with no description text; those are not an automatic pass. Investigate any warning outside the specifically understood baseline before activation. The displayed timer and service must match the approved installed scheduler contract, including the durable state-gate `ExecCondition` and failed-attempt outcome hook. Stop if the timer or any required hook differs; do not change it here. Do not paste credential values, private profile contents, or raw private logs into an issue or repository.

## 2. Safe activation - only after the pre-flight and owner approval

The following is one root-shell block. It adds only `90-sms-group-pilot.conf` to the existing publisher service drop-in directory. It does not modify the base unit, other drop-ins, timer, scheduler state, repository, or public data. It refuses to run near the next timer tick, while the service/publisher/lock is active, or if the existing service contract changed. It reloads systemd but does not restart or start anything. The already-installed timer and durable eligibility gate remain responsible for any later invocation; the activation block does not assume or change the timer cadence and does not force a run.

If activation fails after creating the dedicated file, the trap removes only that file and reloads systemd. If a same-content pilot file already exists, the block is a no-op only when the effective service environment confirms the exact opt-in is already `1`.

```bash
set -Eeuo pipefail
REPO=/opt/vutrulabs/job-tracker-public
SERVICE=vutrulabs-job-tracker-public.service
TIMER=vutrulabs-job-tracker-public.timer
DROPINDIR=/etc/systemd/system/vutrulabs-job-tracker-public.service.d
DROPIN=$DROPINDIR/90-sms-group-pilot.conf
STATE=/var/lib/vutrulabs-job-tracker-public/state.json
LOCK=$REPO/.runtime/publication/publication.lock
CONTENT='[Service]
Environment=JOB_TRACKER_ENABLE_SMS_GROUP=1
'
CREATED=0
TMP=

activation_failure_cleanup() {
    rc=$?
    if [ "$rc" -ne 0 ]; then
        [ -z "$TMP" ] || rm -f -- "$TMP"
        if [ "$CREATED" -eq 1 ]; then
            rm -f -- "$DROPIN"
            systemctl daemon-reload || echo '[ERR] systemd reload failed during activation cleanup.'
        fi
        echo '[ERR] Activation did not complete; do not start the service. Verify opt-in is absent.'
    fi
    exit "$rc"
}
trap activation_failure_cleanup EXIT

test "$(id -u)" -eq 0 || { echo '[ERR] Open a root shell.'; exit 1; }
cd "$REPO"
test "$(pwd -P)" = "$REPO" || { echo '[ERR] Repository path mismatch.'; exit 1; }
test "$(git branch --show-current)" = main || { echo '[ERR] Host checkout is not on main.'; exit 1; }
test -z "$(git status --porcelain=v1 --untracked-files=all)" || {
    echo '[ERR] Host worktree is not clean.'
    exit 1
}
git merge-base --is-ancestor daa9a086c9fadda413d38bb66d5168d1c34f98bd HEAD || {
    echo '[ERR] Host main does not contain PR #25.'
    exit 1
}
systemctl is-active --quiet "$TIMER" || { echo '[ERR] Existing timer is not active; stop.'; exit 1; }
systemctl is-enabled --quiet "$TIMER" || { echo '[ERR] Existing timer is not enabled; stop.'; exit 1; }
systemctl is-active --quiet "$SERVICE" && { echo '[ERR] Publisher service is active; stop.'; exit 1; }
if [ ! -e "$DROPIN" ] && systemctl show -p Environment --value "$SERVICE" |
    tr ' ' '\n' | grep -q '^JOB_TRACKER_ENABLE_SMS_GROUP='; then
    echo '[ERR] SMS opt-in is already set directly in the effective unit environment.'
    exit 1
fi
PASS_ENV=$(systemctl show -p PassEnvironment --value "$SERVICE")
if printf '%s\n' "$PASS_ENV" | tr ' ' '\n' | grep -Exq 'JOB_TRACKER_ENABLE_SMS_GROUP|\*'; then
    echo '[ERR] PassEnvironment could import an unverified SMS opt-in.'
    exit 1
fi
python3 - "$SERVICE" <<'PY'
import os
import re
import shlex
import subprocess
import sys
unit = sys.argv[1]
text = subprocess.check_output(["systemctl", "cat", unit], text=True)
for line in text.splitlines():
    stripped = line.strip()
    if not stripped.startswith("EnvironmentFile="):
        continue
    for path in shlex.split(stripped.split("=", 1)[1]):
        optional = path.startswith("-")
        path = path[1:] if optional else path
        if not os.path.isfile(path):
            if optional:
                continue
            raise SystemExit("[ERR] A required EnvironmentFile is missing.")
        with open(path, encoding="utf-8", errors="replace") as handle:
            if any(re.match(r"^\s*JOB_TRACKER_ENABLE_SMS_GROUP\s*=", item) for item in handle):
                raise SystemExit("[ERR] SMS opt-in is assigned in an EnvironmentFile.")
print("[OK] No EnvironmentFile sets the SMS opt-in.")
PY
pgrep -f '[s]cripts/publish_public_data\.py' >/dev/null && {
    echo '[ERR] A publisher process is active; stop.'
    exit 1
}
if [ -e "$LOCK" ]; then
    exec 9<> "$LOCK"
    flock -n 9 || { echo '[ERR] Publication lock is held; stop.'; exit 1; }
    flock -u 9
    exec 9>&-
fi

WORKDIR=$(systemctl show -p WorkingDirectory --value "$SERVICE")
TYPE=$(systemctl show -p Type --value "$SERVICE")
RESTART=$(systemctl show -p Restart --value "$SERVICE")
EXECSTART=$(systemctl show -p ExecStart --value "$SERVICE")
test "$WORKDIR" = "$REPO" || { echo '[ERR] Publisher working directory changed.'; exit 1; }
test "$TYPE" = oneshot || { echo '[ERR] Publisher service type changed.'; exit 1; }
test "$RESTART" = no || { echo '[ERR] Publisher restart policy changed.'; exit 1; }
case "$EXECSTART" in
    *scripts/publish_public_data.py*) ;;
    *) echo '[ERR] Effective ExecStart is not the reviewed publisher command.'; exit 1 ;;
esac
grep -Fq 'JOB_TRACKER_SCHEDULER_STATE=/var/lib/vutrulabs-job-tracker-public/state.json' \
    "$DROPINDIR/20-scheduler-gate.conf" || {
    echo '[ERR] Existing scheduler-state drop-in is missing or changed.'
    exit 1
}
grep -Fqx 'ExecCondition=/usr/bin/python3 /opt/vutrulabs/job-tracker-public/scripts/hostinger_scheduler_state.py eligible --state-file /var/lib/vutrulabs-job-tracker-public/state.json' \
    "$DROPINDIR/20-scheduler-gate.conf" || {
    echo '[ERR] Existing six-hour scheduler eligibility hook is missing or changed.'
    exit 1
}
grep -Fqx 'ExecStopPost=/usr/bin/python3 /opt/vutrulabs/job-tracker-public/scripts/hostinger_scheduler_state.py record-outcome --state-file /var/lib/vutrulabs-job-tracker-public/state.json --service-result=${SERVICE_RESULT} --invocation-id=${INVOCATION_ID}' \
    "$DROPINDIR/20-scheduler-gate.conf" || {
    echo '[ERR] Existing failed-attempt outcome hook is missing or changed.'
    exit 1
}
test -r "$STATE" || { echo '[ERR] Durable scheduler state is missing.'; exit 1; }
set +e
/usr/bin/python3 "$REPO/scripts/hostinger_scheduler_state.py" eligible \
    --state-file "$STATE" --dry-run
ELIGIBILITY_RC=$?
set -e
case "$ELIGIBILITY_RC" in
    0) echo '[OK] Existing scheduler state is valid and currently eligible.' ;;
    1) echo '[INFO] Existing scheduler state is valid but not due; keep the timer untouched.' ;;
    *) echo '[ERR] Scheduler state validation failed.'; exit "$ELIGIBILITY_RC" ;;
esac
if systemctl show -p NextElapseUSecRealtime --value "$TIMER" | grep -q .; then
    NEXT=$(systemctl show -p NextElapseUSecRealtime --value "$TIMER")
    NEXT_EPOCH=$(date -u -d "$NEXT" +%s)
    NOW_EPOCH=$(date -u +%s)
    test "$NEXT_EPOCH" -gt "$((NOW_EPOCH + 600))" || {
        echo '[ERR] Timer tick is within 10 minutes; retry this block after the tick.'
        exit 1
    }
else
    echo '[ERR] Could not determine the existing timer next tick.'
    exit 1
fi

if [ -e "$DROPIN" ] || [ -L "$DROPIN" ]; then
    test -f "$DROPIN" && ! test -L "$DROPIN" || {
        echo '[ERR] Dedicated SMS drop-in exists but is not a regular file.'
        exit 1
    }
    printf '%s' "$CONTENT" | cmp -s - "$DROPIN" || {
        echo '[ERR] Dedicated SMS drop-in exists with unexpected content; do not overwrite it.'
        exit 1
    }
    systemctl show -p Environment --value "$SERVICE" |
        tr ' ' '\n' | grep -Fxq 'JOB_TRACKER_ENABLE_SMS_GROUP=1' || {
        echo '[ERR] Existing SMS drop-in is not effective; do not start the service.'
        exit 1
    }
    echo '[OK] Exact pilot drop-in is already installed; no change made.'
    trap - EXIT
    exit 0
fi

mkdir -p -m 0755 "$DROPINDIR"
TMP=$(mktemp "$DROPINDIR/.90-sms-group-pilot.XXXXXX")
printf '%s' "$CONTENT" > "$TMP"
chmod 0644 "$TMP"
mv -n -- "$TMP" "$DROPIN"
test ! -e "$TMP" || { echo '[ERR] Dedicated drop-in appeared concurrently; do not overwrite it.'; exit 1; }
TMP=
CREATED=1
systemctl daemon-reload
systemctl show -p Environment --value "$SERVICE" |
    tr ' ' '\n' | grep -Fxq 'JOB_TRACKER_ENABLE_SMS_GROUP=1' || {
    echo '[ERR] Effective service opt-in is not exactly 1.'
    exit 1
}
systemctl is-active --quiet "$TIMER" || { echo '[ERR] Existing timer is no longer active.'; exit 1; }
systemctl is-enabled --quiet "$TIMER" || { echo '[ERR] Existing timer is no longer enabled.'; exit 1; }
systemctl is-active --quiet "$SERVICE" && {
    echo '[ERR] Service unexpectedly became active; do not restart or start it.'
    exit 1
}
echo '[OK] SMS opt-in is isolated in the dedicated service drop-in.'
echo '[OK] Existing timer remains enabled and active; no service run was forced.'
echo '[INFO] Wait for the existing guarded timer invocation; check eligibility and logs privately.'
CREATED=0
trap - EXIT
```

Do not run `systemctl set-environment`, `systemctl start`, `systemctl restart`, or the publisher command. Do not edit or reset scheduler state to make a run due. In particular, do not change the existing timer cadence or the `ExecCondition`, `ExecStopPost`, publication lock, or six-hour retry behavior.

## 3. Live acceptance after the first eligible scheduled invocation

Collect non-secret evidence privately from the service result, committed `data/source_status.json`, committed `data/sms-group/processed/acquisition.json`, the published SMS CSVs, the full audit, and timer/state status. The pilot passes only when all of these are true:

1. `sms-group` has a positive current-job count and the same positive detail count; every current job has matching detail identity/link.
2. `acquisition.json` has `source_id: sms-group`, `company: SMS group`, `acquisition_mode: api`, `adapter: dvinci`, `status: success`, `coverage_complete: true`, a fresh `observed_at`, positive `records_written` equal to the normalized current count, and a nonempty `data_hash`. The bootstrap marker is gone.
3. `source_status.json` lists SMS as attempted and successful, with matching positive `records_written`; it is not unattempted, failed, or incomplete.
4. The normalized SMS output and successful metadata are present in a published GitHub commit on the normal publisher ref. Do not infer publication from local files alone.
5. The full audit returns exit 0 and 0 FAIL. After SMS bootstrap replacement, the only warnings accepted without separate resolution are the independently known stale Tesla/Jacobs warnings. SMS, unknown-location, missing-description, schema, count, provenance, and other unexpected warnings fail acceptance pending investigation.
6. Existing history/change invariants still pass: active history IDs match current IDs; prior history is retained; change types/IDs remain valid; summary totals match current jobs. No history reset or fabricated jobs.
7. SpaceX/Patrick invariants are unchanged: SMS remains absent from Patrick source coverage and rankings; SpaceX and Patrick feed JSON/CSV/Markdown counts and identity/order remain coherent. Compare SpaceX/Patrick counts with the immediately preceding published snapshot and explain any upstream change; SMS must not account for a ranking/count increase.
8. The official d.vinci feed publication IDs and official sitemap IDs are equal as checked by the adapter, and the normalized links remain canonical on the official careers host. This is the provenance/completeness claim supported by the adapter; do not claim one sitemap entry equals one unique opening or that an unqueried detail page was independently verified.
9. The existing timer is still enabled and active. The installed durable state records the publisher outcome and maintains the six-hour interval and six-hour failure backoff. No manual or forced service invocation is used for acceptance.

If source collection fails, do not invent data, populate bootstrap rows, switch to alternate/bypass scraping, or claim SMS is live. If real service logs show the publisher failing on unrelated sources, stop the pilot, roll back the opt-in when safe, and report the exact failure to Engineering Operations. The publisher normally preserves last-good tracked SMS datasets on source failure; its failure and coverage metadata must remain visible.

## 4. Rollback

Run this single block as root after an incident or owner decision. If the publisher is active, do not stop or kill it: wait for it to finish, then rerun the block. The block removes only the dedicated `90-sms-group-pilot.conf`; it does not revert data, alter the existing 20 scheduler drop-in, edit the timer, stop/restart the publisher, or rewrite scheduler state. It leaves already-published last-good snapshots untouched.

```bash
set -euo pipefail
REPO=/opt/vutrulabs/job-tracker-public
SERVICE=vutrulabs-job-tracker-public.service
TIMER=vutrulabs-job-tracker-public.timer
DROPIN=/etc/systemd/system/vutrulabs-job-tracker-public.service.d/90-sms-group-pilot.conf
STATE=/var/lib/vutrulabs-job-tracker-public/state.json
LOCK=$REPO/.runtime/publication/publication.lock
CONTENT='[Service]
Environment=JOB_TRACKER_ENABLE_SMS_GROUP=1
'

test "$(id -u)" -eq 0 || { echo '[ERR] Open a root shell.'; exit 1; }
cd "$REPO"
test "$(pwd -P)" = "$REPO" || { echo '[ERR] Repository path mismatch.'; exit 1; }
systemctl is-active --quiet "$SERVICE" && {
    echo '[ERR] Publisher is active. Do not stop it; wait for completion and retry.'
    exit 1
}
pgrep -f '[s]cripts/publish_public_data\.py' >/dev/null && {
    echo '[ERR] A publisher process is active. Do not stop it; wait and retry.'
    exit 1
}
if [ -e "$LOCK" ]; then
    exec 9<> "$LOCK"
    flock -n 9 || { echo '[ERR] Publication lock is held; wait and retry.'; exit 1; }
    flock -u 9
    exec 9>&-
fi
test -f "$DROPIN" && ! test -L "$DROPIN" || {
    echo '[ERR] Dedicated SMS drop-in is missing or not a regular file; inspect manually.'
    exit 1
}
grep -Fxq '[Service]' "$DROPIN" || { echo '[ERR] Unexpected dedicated drop-in; do not remove it.'; exit 1; }
grep -Fxq 'Environment=JOB_TRACKER_ENABLE_SMS_GROUP=1' "$DROPIN" || {
    echo '[ERR] Unexpected dedicated drop-in content; do not remove it.'
    exit 1
}
test -r "$STATE" || { echo '[ERR] Durable scheduler state is missing; stop.'; exit 1; }
NEXT=$(systemctl show -p NextElapseUSecRealtime --value "$TIMER")
test -n "$NEXT" || { echo '[ERR] Could not determine the existing timer next tick.'; exit 1; }
NEXT_EPOCH=$(date -u -d "$NEXT" +%s)
NOW_EPOCH=$(date -u +%s)
test "$NEXT_EPOCH" -gt "$((NOW_EPOCH + 600))" || {
    echo '[ERR] Timer tick is within 10 minutes; wait until after that tick and retry.'
    exit 1
}
printf '%s' "$CONTENT" | cmp -s - "$DROPIN" || {
    echo '[ERR] Dedicated drop-in has unexpected content; do not remove it.'
    exit 1
}
rm -- "$DROPIN"
if ! systemctl daemon-reload; then
    echo '[ERR] Drop-in was removed, but systemd reload failed; do not start the service and report immediately.'
    exit 1
fi
python3 - "$SERVICE" <<'PY'
import os
import re
import shlex
import subprocess
import sys
unit = sys.argv[1]
sms = "JOB_TRACKER_ENABLE_SMS_GROUP"
text = subprocess.check_output(["systemctl", "cat", unit], text=True)
for line in text.splitlines():
    stripped = line.strip()
    if stripped.startswith("Environment="):
        if any(token.split("=", 1)[0] == sms for token in shlex.split(stripped.split("=", 1)[1])):
            raise SystemExit("[ERR] SMS opt-in remains in a unit/drop-in.")
    if stripped.startswith("EnvironmentFile="):
        for path in shlex.split(stripped.split("=", 1)[1]):
            optional = path.startswith("-")
            path = path[1:] if optional else path
            if not os.path.isfile(path):
                if optional:
                    continue
                raise SystemExit("[ERR] A required EnvironmentFile is missing.")
            with open(path, encoding="utf-8", errors="replace") as handle:
                if any(re.match(r"^\s*" + re.escape(sms) + r"\s*=", item) for item in handle):
                    raise SystemExit("[ERR] SMS opt-in remains in an EnvironmentFile.")
passed = subprocess.check_output(
    ["systemctl", "show", "-p", "PassEnvironment", "--value", unit], text=True
).split()
if sms in passed or "*" in passed:
    raise SystemExit("[ERR] PassEnvironment can still import the SMS opt-in.")
print("[OK] SMS opt-in is absent from remaining unit/drop-ins and EnvironmentFiles.")
PY
systemctl is-active --quiet "$TIMER" || {
    echo '[ERR] Existing timer is not active. Do not change it in this rollback; report to Operations.'
    exit 1
}
systemctl is-enabled --quiet "$TIMER" || {
    echo '[ERR] Existing timer is not enabled. Do not change it in this rollback; report to Operations.'
    exit 1
}
printf '%s\n' '=== SCHEDULER OUTCOME (READ ONLY) ==='
systemctl show "$SERVICE" --no-pager -p Result -p ExecMainStatus -p InactiveEnterTimestamp
/usr/bin/python3 - "$REPO" "$STATE" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from scripts import hostinger_scheduler_state as scheduler
state = scheduler.read_state(Path(sys.argv[2]))
for key in ("last_success_utc", "last_attempt_utc", "last_attempt_status", "last_failure_utc"):
    print(f"{key}={state[key]}")
print("next_attempt_after_utc=" + scheduler.format_utc(
    scheduler.next_attempt_after(Path(sys.argv[2]))
))
PY
if [ -r "$REPO/data/source_status.json" ]; then
    /usr/bin/python3 - "$REPO/data/source_status.json" <<'PY'
import json
import sys
from pathlib import Path
document = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
source = next((item for item in document["sources"] if item["source_id"] == "sms-group"), None)
if source is None:
    raise SystemExit("[ERR] SMS source status is missing.")
for key in ("source_id", "attempted", "status", "coverage_complete", "records_written", "publication_status"):
    print(f"{key}={source.get(key)}")
PY
fi
echo '[OK] Only the dedicated SMS opt-in drop-in was removed; published snapshots and scheduler state were not edited.'
echo '[OK] Existing timer remains enabled and active; normal guarded scheduling is intact.'
echo '[ACTION] Preserve this non-secret state/source-status output in the approved private Operations incident record.'
```

Systemd's existing outcome hook records a failed publisher invocation and applies the six-hour failure backoff. If the publisher reports a non-blocking source warning but exits successfully, its state correctly records success; the SMS failure remains in source-status/acquisition metadata and the operational incident record. Never forge a failed scheduler state or manually change its timestamps. If the publisher itself failed on unrelated sources, stop the SMS pilot and report that failure rather than attempting another run.

## Current verification boundary

The local versioned audit at the PR #25 merge reports 0 failures and exactly 3 expected warnings (Tesla stale, Jacobs stale, and empty SMS bootstrap). This is repository-data evidence only. No live Hostinger terminal, timer, unit, scheduler state, source response, publication, or post-merge production run was verified for this runbook.
