# Hostinger scheduler PR #20 operator runbook

Status: proposed, review-only. Do not run any deployment command until the owner approves the retry policy, bootstrap anchor, catch-up behavior, PR merge, and deployment window. This document does not authorize a manual publication or change the Hostinger installation.

The proposed policy checks eligibility hourly in systemd, but invokes the real publisher only after 48 hours since the last successful publisher execution. The initial failure retry backoff is six hours. The publisher CLI uses the same durable state and publication lock when manually invoked after state is provisioned. Successful no-change runs count as successful executions for cadence, but are not represented as new data publications.

The installed Hostinger service currently uses systemd 255, `Type=oneshot`, `Restart=no`, default root user, and a venv Python executable. The complete effective `ExecStart` was not visible in the screenshots. Re-inspect it on-host; do not replace the service command or assume that CI's synthetic unit is a production integration test. The gate uses UTC wall-clock timestamps; a backward clock step detected before outcome recording fails closed, but a forward clock step can make a run eligible early. Confirm NTP synchronization and avoid manual time changes during an active publisher run.

## 1. Read-only host and service preflight

Run each block in a normal Hostinger root shell. Do not redirect output into the repository, paste private output into GitHub, or include credentials/private profile contents in evidence. Stop if the service is active, the worktree is dirty, the systemd version is below 243, time synchronization is not active, or any existing service security setting differs unexpectedly.

```bash
set -eu
REPO=/opt/vutrulabs/job-tracker-public
cd "$REPO"
test "$(id -u)" -eq 0
printf '%s\n' '=== SYSTEMD ==='
systemd --version
printf '%s\n' '=== SERVICE AND TIMER DEFINITIONS (READ ONLY) ==='
systemctl cat vutrulabs-job-tracker-public.service vutrulabs-job-tracker-public.timer
printf '%s\n' '=== EFFECTIVE SERVICE STATE ==='
systemctl show vutrulabs-job-tracker-public.service -p Type -p Restart -p User -p Group -p WorkingDirectory -p ExecStart -p Environment -p StateDirectory -p ActiveState -p SubState -p Result -p ExecMainStatus -p InactiveEnterTimestamp --no-pager
printf '%s\n' '=== TIMER STATE ==='
systemctl show vutrulabs-job-tracker-public.timer -p ActiveState -p SubState -p LastTriggerUSec -p NextElapseUSecRealtime -p NextElapseUSecMonotonic -p TimersMonotonic --no-pager
printf '%s\n' '=== CLOCK SYNCHRONIZATION ==='
timedatectl status
printf '%s\n' '=== REPOSITORY STATE ==='
git status --short --branch
git branch --show-current
git rev-parse HEAD
```

Decision checkpoint: verify the existing `ExecStart` still uses the approved venv Python and `scripts/publish_public_data.py`, the effective service remains oneshot with no automatic restart, the default root identity is understood, the existing publication lock and security settings are intact, and the current timer still matches the backup target. Do not continue if any line is clipped or ambiguous; obtain the complete output through a private approved channel.

## 2. Back up installed units and state (no changes to active units)

Choose a unique backup directory. This stage reads existing unit/state files and saves copies under root-only storage. It does not stop, reload, or start anything.

```bash
set -eu
TIMER=/etc/systemd/system/vutrulabs-job-tracker-public.timer
DROPIN=/etc/systemd/system/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf
STATE_DIR=/var/lib/vutrulabs-job-tracker-public
BACKUP=/root/vutrulabs-scheduler-backup-$(date -u +%Y%m%dT%H%M%SZ)

test -f "$TIMER"
test ! -e "$BACKUP"
install -d -m 0700 "$BACKUP"
cp -a "$TIMER" "$BACKUP/vutrulabs-job-tracker-public.timer"
if test -e "$DROPIN"; then cp -a "$DROPIN" "$BACKUP/20-scheduler-gate.conf"; else touch "$BACKUP/dropin-was-absent"; fi
if test -e "$STATE_DIR/state.json"; then cp -a "$STATE_DIR/state.json" "$BACKUP/state.json"; else touch "$BACKUP/state-was-absent"; fi
systemctl is-enabled vutrulabs-job-tracker-public.timer > "$BACKUP/timer-enabled" 2>&1 || :
systemctl is-active vutrulabs-job-tracker-public.timer > "$BACKUP/timer-active" 2>&1 || :
printf 'Backup directory: %s\n' "$BACKUP"
```

Checkpoint: keep the printed backup path in the private deployment record, not a public issue or repository file. If `state.json` already exists, stop and inspect its version and values read-only; do not overwrite or initialize it again.

## 3. Stop scheduling and verify service idle

This is the first mutating stage. It stops only the timer; it does not start the publisher or alter datasets. Abort if the publisher is active. Keep the timer stopped through code synchronization, unit installation, state initialization, and static checks.

```bash
set -eu
if systemctl is-active --quiet vutrulabs-job-tracker-public.service; then
    echo '[ERR] Publisher is active; abort deployment and investigate.'
    exit 1
fi
systemctl stop vutrulabs-job-tracker-public.timer
systemctl show vutrulabs-job-tracker-public.timer -p ActiveState -p SubState --no-pager
systemctl show vutrulabs-job-tracker-public.service -p ActiveState -p SubState --no-pager
```

Checkpoint: timer is inactive and service is inactive. Do not continue if the publisher is still active or stopping.

## 4. Synchronize the approved branch

This stage is allowed only after PR #20 has been reviewed and merged by the owner. It updates the existing checkout through a fast-forward only; it does not reset history or directly modify public data snapshots.

```bash
set -eu
REPO=/opt/vutrulabs/job-tracker-public
cd "$REPO"
test -z "$(git status --porcelain)"
git fetch origin
test "$(git branch --show-current)" = main
git pull --ff-only origin main
git status --short --branch
git log -1 --oneline
test -f scripts/hostinger_scheduler_state.py
test -f scripts/check_hostinger_scheduler.py
test -f scripts/systemd/vutrulabs-job-tracker-public.timer
test -f scripts/systemd/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf
```

Checkpoint: confirm the resulting commit includes the approved PR merge, the repository is clean, and all four files exist. Do not run `git reset`, force-push, or edit `data/` as part of scheduler installation.

## 5. Install the versioned units

```bash
set -eu
REPO=/opt/vutrulabs/job-tracker-public
TIMER=/etc/systemd/system/vutrulabs-job-tracker-public.timer
DROPIN_DIR=/etc/systemd/system/vutrulabs-job-tracker-public.service.d
DROPIN=$DROPIN_DIR/20-scheduler-gate.conf

install -d -m 0755 "$DROPIN_DIR"
install -d -m 0700 /var/lib/vutrulabs-job-tracker-public
chmod 0700 /var/lib/vutrulabs-job-tracker-public
install -m 0644 "$REPO/scripts/systemd/vutrulabs-job-tracker-public.timer" "$TIMER"
install -m 0644 "$REPO/scripts/systemd/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf" "$DROPIN"
```

Checkpoint: inspect the installed files with `systemctl cat`. Confirm the drop-in adds only `StateDirectory`, `StateDirectoryMode=0700`, the scheduler state path, `ExecCondition`, and `ExecStopPost`; the original service `ExecStart`, root identity, working directory, lock behavior, and all other security settings must remain intact. The state directory is root-owned mode 0700 and state files are atomically written mode 0600; this is compatible with the verified default root service and root-run publisher CLI.

## 6. Initialize the durable state exactly once

Use the most recent successful publisher invocation timestamp only if verified from complete journal evidence. A Git commit timestamp is not sufficient because a successful no-change run creates no commit. The October 15 data publication is the latest verified new public dataset; later successful no-change executions have not been ruled out.

First verify no state file exists:

```bash
test ! -e /var/lib/vutrulabs-job-tracker-public/state.json
```

If the latest successful invocation is known, initialize with its UTC timestamp:

```bash
REPO=/opt/vutrulabs/job-tracker-public
STATE=/var/lib/vutrulabs-job-tracker-public/state.json
LAST_SUCCESS_UTC='YYYY-MM-DDTHH:MM:SSZ'
/usr/bin/python3 "$REPO/scripts/hostinger_scheduler_state.py" initialize --state-file "$STATE" --last-success-utc "$LAST_SUCCESS_UTC"
```

If it cannot be proven, do not invent one. Initialize a conservative first-run barrier at least 48 hours from initialization:

```bash
REPO=/opt/vutrulabs/job-tracker-public
STATE=/var/lib/vutrulabs-job-tracker-public/state.json
FIRST_RUN_AFTER_UTC=$(date -u -d '+48 hours 1 second' +%Y-%m-%dT%H:%M:%SZ)
/usr/bin/python3 "$REPO/scripts/hostinger_scheduler_state.py" initialize --state-file "$STATE" --first-run-after-utc "$FIRST_RUN_AFTER_UTC"
printf 'First eligible time: %s\n' "$FIRST_RUN_AFTER_UTC"
```

The conservative option leaves currently stale public data stale for at least another 48 hours plus up to one hourly slot. The latest verified data publication is October 15; as of the October 20 preflight it is already over 60 hours old. If fresher data is operationally necessary, request explicit owner authorization for a one-time manual publication; do not infer that approval from this runbook or bypass the new gate.

## 7. Dry checks and static unit verification

These checks do not start a service or modify scheduler state. `eligible --dry-run` is safe even when the run is currently due.

```bash
set -eu
REPO=/opt/vutrulabs/job-tracker-public
STATE=/var/lib/vutrulabs-job-tracker-public/state.json
systemd-analyze verify /etc/systemd/system/vutrulabs-job-tracker-public.timer /etc/systemd/system/vutrulabs-job-tracker-public.service
systemd-analyze calendar '*-*-* *:00:00 UTC'
systemd-analyze calendar '*-*-1/2 02:00:00 UTC'
if /usr/bin/python3 "$REPO/scripts/hostinger_scheduler_state.py" eligible --state-file "$STATE" --dry-run; then
    echo '[OK] Eligibility check is currently due (dry run only).'
else
    result=$?
    test "$result" -eq 1
    echo '[INFO] Eligibility check is not due; no scheduler state was changed.'
fi
if /usr/bin/python3 "$REPO/scripts/check_hostinger_scheduler.py" --state-file "$STATE"; then
    :
else
    result=$?
    test "$result" -eq 1
fi
```

The smoke check runs only `systemctl show` and reads state. A nonzero result because the timestamp is unknown or older than 60 hours is an alert, not a reason to bypass the gate. `systemd-analyze verify` must validate the installed unit plus the actual service; inspect `systemctl cat` separately because a static synthetic CI unit is not the host service.

Checkpoint: decide whether an overdue persisted success timestamp may cause an immediate `Persistent=true` catch-up after activation. If that is not approved, the conservative future anchor must be used. Owner must also explicitly approve the proposed six-hour retry cooldown. Do not continue without both decisions.

## 8. Reload, enable, and verify without manually starting publisher

This stage may cause a persistent catch-up activation. It is a production scheduling change and requires the approved deployment window.

```bash
set -eu
systemctl daemon-reload
systemctl enable --now vutrulabs-job-tracker-public.timer
systemctl show vutrulabs-job-tracker-public.timer -p ActiveState -p SubState -p LastTriggerUSec -p NextElapseUSecRealtime -p NextElapseUSecMonotonic -p Persistent --no-pager
systemctl list-timers --all vutrulabs-job-tracker-public.timer --no-pager
systemctl show vutrulabs-job-tracker-public.service -p Type -p Restart -p User -p Group -p WorkingDirectory -p ExecStart -p StateDirectory -p ActiveState -p Result -p ExecMainStatus --no-pager
```

Do not run `systemctl start vutrulabs-job-tracker-public.service` or invoke the publisher manually as a substitute. A timer-triggered service start will pass through the gate. The direct CLI is also gated and updates shared state after installation.

## 9. Post-reboot and unattended acceptance

On a non-production staging host, verify reboot and missed-hour catch-up using a harmless test service. Expect one catch-up activation at most, no production attempt before the state deadline or during six-hour retry backoff, and at most one automatic attempt per eligible hourly slot. Do not reboot or stop the production timer for testing.

After the first approved unattended production opportunity:

```bash
systemctl show vutrulabs-job-tracker-public.timer -p LastTriggerUSec -p NextElapseUSecRealtime --no-pager
systemctl show vutrulabs-job-tracker-public.service -p Result -p ExecMainStatus -p ExecMainStartTimestamp -p ExecMainExitTimestamp --no-pager
journalctl -o short-iso-precise -u vutrulabs-job-tracker-public.timer -u vutrulabs-job-tracker-public.service --since '48 hours ago' --no-pager
/usr/bin/python3 /opt/vutrulabs/job-tracker-public/scripts/check_hostinger_scheduler.py
```

Accept only a successful publisher execution, current durable success timestamp, coherent current source status/data timestamps, and journal evidence for any failed-source reporting. A successful no-change run may have no new commit. Record only redacted operational facts (timestamps, result code, freshness and commit SHA when public) in a follow-up documentation update; never commit credentials, private profiles, raw logs containing secrets, or private data.

## 10. Rollback

Keep the state file for audit and do not delete it. Restore the code version through an approved revert PR and fast-forward pull; do not reset or detach the Hostinger checkout. While the PR's publisher code remains installed, it will continue to enforce state eligibility even if only the timer/drop-in is restored, so a unit-only rollback is not a complete rollback of the cadence gate.

First open and merge an owner-approved revert PR for the scheduler code. Do not reset the Hostinger checkout or revert public data. Stop the timer, then fast-forward the existing main checkout to the merged revert:

```bash
set -eu
REPO=/opt/vutrulabs/job-tracker-public
cd "$REPO"
test -z "$(git status --porcelain)"
systemctl stop vutrulabs-job-tracker-public.timer
git fetch origin
test "$(git branch --show-current)" = main
git pull --ff-only origin main
git status --short --branch
git log -1 --oneline
```

After confirming that the reviewed revert removed the scheduler publisher integration, use the private backup directory recorded in stage 2. Restore the prior timer and prior drop-in (or remove only the newly introduced drop-in if it did not previously exist), reload systemd, and restore the original enabled/running state:

```bash
set -eu
TIMER=/etc/systemd/system/vutrulabs-job-tracker-public.timer
DROPIN=/etc/systemd/system/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf
BACKUP=/root/vutrulabs-scheduler-backup-YYYYMMDDTHHMMSSZ

test -f "$BACKUP/vutrulabs-job-tracker-public.timer"
systemctl stop vutrulabs-job-tracker-public.timer
install -m 0644 "$BACKUP/vutrulabs-job-tracker-public.timer" "$TIMER"
if test -e "$BACKUP/dropin-was-absent"; then rm -f "$DROPIN"; else install -m 0644 "$BACKUP/20-scheduler-gate.conf" "$DROPIN"; fi
systemctl daemon-reload
case "$(cat "$BACKUP/timer-enabled")" in
    enabled|enabled-runtime|linked|linked-runtime|alias) systemctl enable vutrulabs-job-tracker-public.timer ;;
    *) systemctl disable vutrulabs-job-tracker-public.timer ;;
esac
if test "$(cat "$BACKUP/timer-active")" = active; then systemctl start vutrulabs-job-tracker-public.timer; else systemctl stop vutrulabs-job-tracker-public.timer; fi
systemctl show vutrulabs-job-tracker-public.timer -p ActiveState -p SubState -p LastTriggerUSec -p NextElapseUSecRealtime --no-pager
```

The old monotonic timer's activation origin is reset by rollback. Its reliability is not established by this PR. Do not treat rollback as successful scheduler acceptance.
