# Copilot / Engineering Operations — Make Hostinger scheduler restart-safe

Date: 2026-10-19. Repo: `hailbagel/job-tracker-public`.

## Decision and confirmed facts

**Do not call the unattended 48-hour publisher production-verified.**

The user supplied direct Hostinger screenshots of:

```ini
# /etc/systemd/system/vutrulabs-job-tracker-public.timer
[Unit]
Description=VuTruLabs Job Tracker Public 48-hour publisher timer

[Timer]
OnActiveSec=48h
OnUnitInactiveSec=48h
AccuracySec=1min
RandomizedDelaySec=0
Unit=vutrulabs-job-tracker-public.service

[Install]
WantedBy=timers.target
```

Further observed facts:

- Publication at **2026-10-15 13:47:18 UTC** was successful and pushed commit `a8ba2fc`; Tesla and Jacobs were separately marked as failed sources while five sources and the Patrick feed succeeded.
- Timer stopped **2026-10-17 12:40:01 UTC** and started **2026-10-17 13:05:02 UTC**. The screenshot shows a boot ID in the journal output, but not enough to establish why the timer was restarted.
- On **2026-10-19 ~04:06 UTC**, timer was `active (waiting)`, `LastTriggerUSec=` empty and `NextElapseUSecRealtime=` empty. Systemd reported **NEXT 2026-10-21 02:52:19 UTC** and **LAST = -**.
- The 21 October deadline appears **much later than 48 hours after the 17 October activation**. Do NOT hand-wave this mismatch; correlate monotonic clock progress, reboot/suspend behavior and service unit states. We have not independently identified the exact origin of this discrepancy.
- No newer successfully pushed dataset exists after 15 October (as of the user's 19 October screenshot).
- The new SMS group, Midrex, Mesabi Metallics, and Siemens AG registry entries are `manual_discovery`. They are NOT automated and did not cause a publishing failure in the observed output.

## Additional host evidence received 2026-10-19 (read-only)

The requested Hostinger diagnostic returned:

```text
Mon Oct 19 04:10:34 UTC 2026
uptime -s: 2026-10-17 13:04:54
/proc/uptime: 140739.35 126696.97
NextElapseUSecMonotonic=3d 13h 47min 24.246860s
LastTriggerUSec=
LastTriggerUSecMonotonic=0
ActiveEnterTimestamp=Sat 2026-10-17 13:05:02 UTC
ActiveEnterTimestampMonotonic=8074892
```

**Calculated:**
- Boot at 2026-10-17 13:04:54 UTC; timer activation eight seconds later.
- `OnActiveSec=48h` would nominally place its first monotonic deadline at approximately 2026-10-19 13:05:02 UTC.
- Actual next deadline was shown as 2026-10-21 02:52:19 UTC, approximately **37 hours 47 minutes later** than the activation-relative 48h candidate.
- `NextElapseUSecMonotonic` is a monotonic timestamp relative to boot, not a countdown or an actual service run. It maps to the Oct 21 NEXT time when added to the boot timestamp.
- `LastTriggerUSecMonotonic=0` and blank `LastTriggerUSec` indicate **no last trigger recorded by this currently active timer instance**. They do not independently prove that no past timer run ever occurred.
- This result rules out merely misreading the UTC/CEST offset as an explanation. The additional ~37h47m deviation cannot be explained by `AccuracySec=1min` and `RandomizedDelaySec=0`.
- Still unknown: precise systemd service unit state transitions, `InactiveEnterTimestampMonotonic` and any manager state carried over during the reboot, which may affect `OnUnitInactiveSec` calculations. **Do not claim a fully proven low-level root cause.**

**Preferred engineering direction:** propose fixed wall-clock calendar eligibility checks with `Persistent=true`, plus durable last-success state and a 48h publishing eligibility gate if the owner requires a strict rolling interval. If an *approximately every 48h* fixed-slot policy is sufficient, compare a simpler explicitly scheduled calendar variant. Note that using `OnCalendar=*-*-* ...` on the existing unguarded publishing service would execute the real scraper daily, which is **not acceptable without changing the cadence contract**.

Use the original publisher service and security invariants; do not immediately change the host. Provide the full proposed units, a test against boot/restart and missed schedules, rollback commands and a PR. Include a separate check that identifies when publication is stale even if systemd reports `Result=success` from an earlier run.

### If deeper unit-state correlation is required

Read-only one-liner, run only if needed before finalizing a patch:

```bash
systemctl show vutrulabs-job-tracker-public.service -p ActiveState -p SubState -p InactiveEnterTimestamp -p InactiveEnterTimestampMonotonic -p ExecMainStatus --no-pager && systemctl show vutrulabs-job-tracker-public.timer -p TimersMonotonic -p NextElapseUSecMonotonic -p ActiveEnterTimestampMonotonic --no-pager
```

No service start or timer modification is authorized.

## Technical interpretation to validate

Per the [systemd.timer(5) documentation](https://www.freedesktop.org/software/systemd/man/latest/systemd.timer.html), `OnActiveSec=` measures time since *timer activation*; `OnUnitInactiveSec=` measures time since the triggered service was last deactivated. Both are monotonic timers. If the timer unit is stopped/restarted, its activation-origin changes. Monotonic timers do not inherently catch up across downtime the same way `OnCalendar=` with `Persistent=true` can. Verify this against the installed systemd version and current systemd state before designing a change.

Do not claim the timer definitely failed only because a publication commit is absent: successful runs can finish without publishing a new commit when output is identical. In this case, the timer's empty LAST and the visible journal ending on 15 October warrant investigation.

## Deliverables

1. Produce a **root-cause report** from the existing Hostinger evidence, then list any evidence needed to explain the unusual 21 October NEXT.
2. Propose a **restart-safe scheduler** that targets the owner's existing *approximately 48-hour* cadence, survives reboot and temporary VM downtime, and has a clearly defined catch-up policy. Distinguish precisely between:
   - fixed wall-clock calendar slots (robust with `Persistent=true` but not necessarily an exact continuously sliding 48-hour interval), and
   - strict rolling 48 hours since the last successful publication (requires durable state and a gated calendar check, or an equivalent proven mechanism).
3. Choose the **simplest feasible design** after owner approval; avoid introducing new infrastructure. Do not silently change the requested cadence to hourly or daily production runs. A daily *read-only time eligibility check* may be proposed, but production frequency must remain explicit.
4. Include full versioned proposed `.timer`/`.service` unit files or drop-ins and exact reversible deployment/rollback commands. The currently installed unit under `/etc/systemd/system` is **not** tracked by GitHub: do not pretend a Git commit changes it.
5. Include checks for `systemd-analyze verify`, `systemd-analyze calendar` (for calendar expressions), `systemctl show` deadline/trigger properties, next two expected wall-clock activations, post-reboot behavior, and a journal-based acceptance check after an unattended run.
6. Preserve the existing service command, existing lock / clean-worktree / fail-closed publishing safeguards, the currently approved `data/` schema, 48-hour target, and error reporting for Tesla/Jacobs. Do not bypass permissions, reset Git history or modify private credentials.
7. If a safe rollback/catch-up plan requires a one-time manual publication, request explicit approval; **do not execute it** during code review.
8. Provide a focused smoke-test that only inspects systemd state and reports last successful publication timestamp/freshness; optionally propose an alert if `observed_at` has been stale for more than 60 hours.

## Read-only follow-up for the missing timing evidence

Operator must use an ordinary Hostinger root terminal (no `>` continuation prompt). Copy **exactly one line**:

```bash
date -u && uptime -s && cat /proc/uptime && systemctl show vutrulabs-job-tracker-public.timer -p ActiveEnterTimestamp -p ActiveEnterTimestampMonotonic -p LastTriggerUSec -p LastTriggerUSecMonotonic -p NextElapseUSecRealtime -p NextElapseUSecMonotonic --no-pager && systemctl show vutrulabs-job-tracker-public.service -p ActiveState -p ExecMainStatus -p InactiveEnterTimestamp -p InactiveEnterTimestampMonotonic --no-pager
```

Read-only: no service runs, no reload/restart, no writes.

## Owner cadence clarification — 19 October 2026

**Proposed policy for the Copilot scheduler design:** the owner prioritizes an approximately 48-hour, restart-safe execution interval without hammering upstream sites. Avoid the wording "strict rolling 48h" for a **once-daily check**, because it can delay actual execution until almost 72 hours after the last success.

For the design PR (not a deployment approval):

1. Use a persistent calendar-triggered **eligibility check every hour** (not an hourly production collection). Keep the eligibility check inexpensive, locally read-only except for necessary durable run bookkeeping, and ensure it cannot trigger multiple publishers concurrently.
2. Allow the normal production collection only when the recorded last completed **successful run** is at least 48 hours old; on a healthy server the next run should occur approximately 48–49 hours after success. Preserve the distinction between successful data publication and zero-output/no-change runs.
3. Preserve a durable, atomic and restart-safe last-success timestamp *and* last-attempt/failure timestamp outside public versioned `data/`, with clear ownership, filesystem permissions, and recovery semantics. Avoid duplicate runs on boot, timer restart, time adjustment, DST, or concurrent checks.
4. **Failure backoff:** If eligible but a production attempt fails, never start a new full collection at every subsequent hourly check. Apply an explicit bounded retry policy (initial recommendation: no more than one automated retry per 6 hours; alert on persistent failure) and ensure failed/incomplete required feed coverage does not count as success. This retry policy requires explicit owner sign-off before live installation.
5. Clarify whether the target is 48 hours since the last **successful** run vs 48 hours since the last **attempt** and document what happens when the upstream providers remain unavailable. Prefer a credible last-success target with bounded failed-attempt backoff and explicit stale-data alerts over pretending to guarantee freshness through upstream outages.
6. Existing `vutrulabs-job-tracker-public.service`, publication locks, Git safeguards, permissions and 48-hour production target remain unchanged unless a tested, reviewed modification is strictly necessary.
7. Include the alternative simpler fixed-calendar 48h design in the PR rationale (and describe its month-boundary/calendar semantics), but recommend the hourly *eligibility-only* approach if the owner requires rolling near-48h execution.
8. Write all associated unit files, guard code, tests, migration steps, rollback steps and exact Hostinger commands into Git. **Do not merge, activate the timer, or run production during the design task.**

**Owner-facing Copilot custom answer to submit:**

> Choose a restart-safe rolling 48-hour cadence. Check eligibility hourly without collecting any data; run the real publisher only after 48 hours since the last successful completion. Persist last success and last attempt across reboots, prevent concurrent/duplicate runs, and throttle failed attempts (propose a 6-hour minimum retry delay with alerts). Do not use daily eligibility checks that permit ~72-hour gaps. Document and test everything in a feature branch and PR; no Hostinger changes or production runs until I approve.

## Git workflow

Create a **feature branch + PR** for the reviewed timer repair design and tests. Keep all prompts, units and operating decisions committed. Do not merge/deploy before owner approval. Link the eventual acceptance evidence (journal, service result, fresh data timestamp) in a follow-up documentation commit.

## Root-cause report and evidence limits

**Conclusion:** the available evidence establishes that the current timer instance had not recorded a trigger by the 2026-10-19 diagnostic, and that its next monotonic deadline did not match the first deadline implied by the displayed `OnActiveSec=48h` configuration. It does **not** establish the low-level cause of the discrepancy or prove that the timer never ran in a prior instance.

The activation-relative candidate was about 2026-10-19 13:05:02 UTC. The displayed NEXT was 2026-10-21 02:52:19 UTC, around 37h47m later. The host booted at 2026-10-17 13:04:54 UTC, the timer activated eight seconds later, and the monotonic timestamp maps to the displayed NEXT. UTC/local-time confusion and the configured one-minute accuracy window do not account for that difference. The exact service state transitions, the timer manager's carried state, and the installed systemd version remain unobserved.

The successful 2026-10-15 publication and push of `a8ba2fc` is evidence of that run only. An absent later commit does not prove that the publisher did not run: a successful unchanged-data run can exit successfully without creating a commit. The empty `LastTriggerUSec` and journal ending on October 15 warrant investigation, but are not proof of a complete run history. Tesla and Jacobs were explicitly reported as failed sources in the October 15 run; the other sources and Patrick feed succeeded. These provider failures are independent of the timer discrepancy. The newer manual-discovery registry entries are not scheduled sources.

The facts above and the host screenshots are historical operator evidence. No Hostinger command was run for this change. Before installation, obtain the installed `systemd --version`, complete unit definitions and drop-ins, `systemctl show` state, timer/service journals, and time-sync status. In particular, correlate `InactiveEnterTimestampMonotonic` for the service with timer `TimersMonotonic`, `NextElapseUSecMonotonic`, and activation time. Do not claim a proven low-level root cause until that evidence explains the mismatch.

## Owner-approved cadence contract

The owner selected **strict rolling 48 hours**. The proposed timer checks eligibility once per hour; an hourly check is not an hourly production run. The existing publisher command executes only when at least 48 hours have elapsed since its last successful invocation. Under a healthy timer, successful publisher executions will be at least 48 and at most approximately 49 hours apart. Failed attempts do not advance the durable success timestamp.

The alternative simpler fixed-slot expression is `OnCalendar=*-*-1/2 02:00:00 UTC` with `Persistent=true`. It selects every other day-of-month, but the sequence resets at each month: in a 31-day month, the activation on day 31 is followed by day 1 only 24 hours later. It therefore is not a strict rolling 48-hour schedule. Any daily/hourly calendar schedule attached directly to an unguarded publisher would run production at that frequency and is rejected. The strict rolling design below uses only systemd and a small durable state file; it adds no service, storage system, Python package, or data-schema change.

### Proposed versioned units

These checked-in files are the proposed host configuration. The timer is a complete unit; the service file is intentionally a drop-in so it does not replace or re-specify the existing service command, user, sandbox, lock, worktree checks, publication allowlist, credentials, or provider error behavior:

- [`scripts/systemd/vutrulabs-job-tracker-public.timer`](../scripts/systemd/vutrulabs-job-tracker-public.timer)
- [`scripts/systemd/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf`](../scripts/systemd/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf)
- [`scripts/hostinger_scheduler_state.py`](../scripts/hostinger_scheduler_state.py)

The timer's sole calendar event is `*-*-* *:00:00 UTC`, with `Persistent=true`, `AccuracySec=1min`, and no randomized delay. The service drop-in's `ExecCondition` checks the 48-hour threshold and a six-hour retry backoff, and atomically records an attempt before allowing the unchanged `ExecStart` to run. `ExecStartPost` records the successful completion time only after the existing publisher exits successfully; `ExecStopPost` records a failed attempt from systemd's `SERVICE_RESULT`. Both callbacks must match the active systemd `INVOCATION_ID`, so a skipped hourly check cannot rewrite a previous attempt's failure time. A missing, malformed, unwritable, or incompatible state file fails closed; it is not treated as permission to publish. The state is atomically replaced and fsynced under `/var/lib/vutrulabs-job-tracker-public/`; it contains timestamps and outcome markers only, not credentials.

The initial proposed failure backoff is a minimum of six hours after a failed attempt completes. This prevents hourly retries from repeatedly scraping upstreams. **Owner sign-off on the six-hour retry policy is required before live installation.** The retry does not count as a success and does not reset the rolling 48-hour success target. Persistent failures should raise an operational alert rather than imply fresh data.

The state timestamp represents the last completed successful publisher run. A run that creates and pushes a data commit is reported separately in the existing journal output from a successful no-change run; both are successful completed runs for the 48-hour scheduler interval, but a no-change run is never described as a new data publication. The smoke check labels its timestamp as a publisher execution, while the journal and public data metadata establish whether new data was actually pushed.

`ExecCondition` requires systemd 243 or newer ([systemd.service(5)](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html)). Check `systemd --version` on the actual host before deploying. The installed Hostinger version and the existing service command have not been verified from the evidence supplied, so installation is blocked until both are inspected. The gate uses synchronized UTC wall-clock time; a clock that steps forward can make a run eligible earlier, while a clock that steps backward delays eligibility. Verify time synchronization before enabling the timer.

### Eligibility bootstrap and catch-up policy

Initialize the state exactly once before enabling the timer:

- Prefer `--last-success-utc` with the most recent successful **publisher invocation** verified in the complete Hostinger journal. Do not use the latest Git commit time as a substitute: a successful no-change run need not commit.
- If a successful invocation time cannot be established, use `--first-run-after-utc` set to at least 48 hours after deployment. This records no fictitious success and conservatively delays the first run. Do not initialize from the October 15 push alone if later no-change runs cannot be ruled out.
- Initialization refuses to overwrite state. Never delete or reset this state during routine rollback.

After downtime, `Persistent=true` causes one catch-up activation for missed calendar events, not one activation per missed hour. The gate starts the publisher only if its 48-hour threshold and retry backoff are both met. Otherwise the check skips, and the next opportunity is the next hourly slot. A publisher failure records its attempt/failure time but does not update success; the gate blocks further retries for at least six hours after the failure, then retries at the next hourly slot. After a successful catch-up, the new success timestamp blocks further production executions for 48 hours. The systemd service manager serializes activations of this unit, the invocation ID fences state callbacks to their own service run, and the existing publication lock remains authoritative against concurrent/manual invocations.

Enabling a persistent timer with an overdue, verified success timestamp may cause an immediate catch-up activation. Review the initialized deadline and approve that possibility before enabling. This PR does not run a manual publication or modify the Hostinger timer. If an immediate catch-up is not approved, use the conservative first-run anchor. No one-time manual publication is required by this rollback plan.

### Focused read-only freshness check

[`scripts/check_hostinger_scheduler.py`](../scripts/check_hostinger_scheduler.py) runs only `systemctl show` and reads the durable state file. It does not start/stop units, reload systemd, inspect Git credentials, or modify files. It reports timer deadline/trigger fields, service `Result`/exit status, and the timestamp and age of the last successful publisher execution. It exits nonzero if that timestamp is unknown or older than 60 hours. Thus a stale prior `Result=success` is not mistaken for a fresh publication. The timestamp measures successful validated publisher execution, not necessarily a new Git commit; an unchanged dataset is a valid no-change success.

```bash
sudo /usr/bin/python3 /opt/vutrulabs/job-tracker-public/scripts/check_hostinger_scheduler.py
```

`data/source_status.json` and source `acquisition.json` `observed_at` values remain the separate data-freshness evidence. An optional independent alert may warn when the newest successful automated-source `observed_at` is over 60 hours old; it must not trigger or bypass the publisher.

### Pre-deployment verification and acceptance

These commands are for an approved Hostinger deployment window only; they were not run as part of this review. First inspect the real service and confirm that its effective `ExecStart` is still the approved `python3 scripts/publish_public_data.py` command and its current security/lock settings are unchanged:

```bash
systemd --version
systemctl cat vutrulabs-job-tracker-public.service vutrulabs-job-tracker-public.timer
systemctl show vutrulabs-job-tracker-public.service -p User -p Group -p ExecStart -p ActiveState -p SubState -p Result -p ExecMainStatus -p InactiveEnterTimestamp -p InactiveEnterTimestampMonotonic --no-pager
systemctl show vutrulabs-job-tracker-public.timer -p ActiveState -p SubState -p LastTriggerUSec -p LastTriggerUSecMonotonic -p NextElapseUSecRealtime -p NextElapseUSecMonotonic -p TimersMonotonic --no-pager
timedatectl status
```

After staging the versioned timer/drop-in and initializing state, but before enabling the timer:

```bash
systemd-analyze verify /etc/systemd/system/vutrulabs-job-tracker-public.timer /etc/systemd/system/vutrulabs-job-tracker-public.service
systemd-analyze calendar '*-*-* *:00:00 UTC'
python3 -c 'from datetime import datetime, timedelta, timezone; now=datetime.now(timezone.utc); first=now.replace(minute=0, second=0, microsecond=0); first += timedelta(hours=(first <= now)); print("NEXT 1:", first.isoformat()); print("NEXT 2:", (first + timedelta(hours=1)).isoformat())'
```

The calendar parser must accept the expression. The Python line displays the next two future hourly UTC slots; compare the first with systemd's calculated next elapse. After `systemctl daemon-reload` and the separately approved timer enable/restart, verify the active unit and deadline without starting the service:

```bash
systemctl show vutrulabs-job-tracker-public.timer -p ActiveState -p SubState -p LastTriggerUSec -p LastTriggerUSecMonotonic -p NextElapseUSecRealtime -p NextElapseUSecMonotonic -p Persistent --no-pager
systemctl list-timers --all vutrulabs-job-tracker-public.timer --no-pager
sudo /usr/bin/python3 /opt/vutrulabs/job-tracker-public/scripts/check_hostinger_scheduler.py
```

Use the focused Python test to exercise the 47h59m59s and 48h-minus-one-microsecond rejection, exact 48h eligibility, durable state across process restart, missed hourly slots, catch-up success resetting the interval, six-hour retry backoff after failure, malformed/missing-state fail-closed behavior, and stale state despite `Result=success`:

```powershell
python -m unittest discover -s tests -p test_hostinger_scheduler.py
```

On a non-production staging host, separately verify `Persistent=true` through a controlled timer stop spanning one or more hourly UTC slots, then reactivation: expect at most one catch-up activation; use a test service there, not the production publisher. Also verify the natural post-reboot case: one catch-up at most, gate skipped if the 48-hour threshold or failure backoff is not met, no duplicate execution during the following hour, and no retries more frequently than once per six hours after a failed completion. A production reboot/timer stop is not authorized by this PR.

After an approved unattended production run, inspect both unit results and journal evidence:

```bash
systemctl show vutrulabs-job-tracker-public.timer -p LastTriggerUSec -p NextElapseUSecRealtime --no-pager
systemctl show vutrulabs-job-tracker-public.service -p Result -p ExecMainStatus -p ExecMainStartTimestamp -p ExecMainExitTimestamp --no-pager
journalctl -u vutrulabs-job-tracker-public.timer -u vutrulabs-job-tracker-public.service --since '48 hours ago' --no-pager
sudo /usr/bin/python3 /opt/vutrulabs/job-tracker-public/scripts/check_hostinger_scheduler.py
```

Accept only an in-window successful publisher execution and successful state-record message in the journal, a fresh state timestamp, and current data/source status. Confirm Tesla/Jacobs failures remain explicitly reported if they recur; they do not by themselves mean the other validated sources or Patrick feed failed. A no-change run may have no new pushed commit, so do not require a new commit as the sole success signal. Record the journal excerpt, `Result`/exit status, state freshness, and relevant `observed_at` evidence in a follow-up documentation commit.

### Reversible Hostinger deployment and rollback

Do not run these commands before owner approval, PR review/merge, and the pre-deployment checks above. The GitHub PR versions configuration only; it does not change `/etc/systemd/system` on Hostinger. Run from the existing Hostinger repository checkout after the approved change has been made available there. Replace no service command and do not modify credentials or data.

```bash
set -eu
REPO=/opt/vutrulabs/job-tracker-public
TIMER=/etc/systemd/system/vutrulabs-job-tracker-public.timer
DROPIN_DIR=/etc/systemd/system/vutrulabs-job-tracker-public.service.d
DROPIN=$DROPIN_DIR/20-scheduler-gate.conf
BACKUP=/root/vutrulabs-scheduler-backup-$(date -u +%Y%m%dT%H%M%SZ)

test ! -e "$BACKUP"
if systemctl is-active --quiet vutrulabs-job-tracker-public.service; then echo "[ERR] Publisher is active; stop and review before deployment"; exit 1; fi
install -d -m 0700 "$BACKUP"
cp -a "$TIMER" "$BACKUP/vutrulabs-job-tracker-public.timer"
if test -e "$DROPIN"; then cp -a "$DROPIN" "$BACKUP/20-scheduler-gate.conf"; else touch "$BACKUP/dropin-was-absent"; fi
systemctl is-enabled vutrulabs-job-tracker-public.timer > "$BACKUP/timer-enabled" 2>&1 || :
systemctl is-active vutrulabs-job-tracker-public.timer > "$BACKUP/timer-active" 2>&1 || :
systemctl stop vutrulabs-job-tracker-public.timer
install -d -m 0755 "$DROPIN_DIR" /var/lib/vutrulabs-job-tracker-public
install -m 0644 "$REPO/scripts/systemd/vutrulabs-job-tracker-public.timer" "$TIMER"
install -m 0644 "$REPO/scripts/systemd/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf" "$DROPIN"
```

Initialize once with the verified latest successful invocation timestamp:

```bash
STATE=/var/lib/vutrulabs-job-tracker-public/state.json
LAST_SUCCESS_UTC='YYYY-MM-DDTHH:MM:SSZ'
/usr/bin/python3 "$REPO/scripts/hostinger_scheduler_state.py" initialize --state-file "$STATE" --last-success-utc "$LAST_SUCCESS_UTC"
```

If the journal cannot establish that timestamp, use a conservative first-run barrier instead:

```bash
STATE=/var/lib/vutrulabs-job-tracker-public/state.json
FIRST_RUN_AFTER_UTC=$(date -u -d '+48 hours' +%Y-%m-%dT%H:%M:%SZ)
/usr/bin/python3 "$REPO/scripts/hostinger_scheduler_state.py" initialize --state-file "$STATE" --first-run-after-utc "$FIRST_RUN_AFTER_UTC"
```

Do not run both initialization alternatives. Continue only after checking the catch-up deadline, obtaining explicit owner sign-off for the six-hour failure retry policy, and approving whether a due persistent catch-up may run immediately:

```bash
systemd-analyze verify "$TIMER" /etc/systemd/system/vutrulabs-job-tracker-public.service
systemd-analyze calendar '*-*-* *:00:00 UTC'
systemctl daemon-reload
systemctl enable --now vutrulabs-job-tracker-public.timer
systemctl show vutrulabs-job-tracker-public.timer -p ActiveState -p SubState -p LastTriggerUSec -p NextElapseUSecRealtime -p Persistent --no-pager
```

Rollback (keep the timestamp state for audit; do not delete it). Set `BACKUP` to the exact directory printed/created during deployment:

```bash
set -eu
TIMER=/etc/systemd/system/vutrulabs-job-tracker-public.timer
DROPIN=/etc/systemd/system/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf
BACKUP=/root/vutrulabs-scheduler-backup-YYYYMMDDTHHMMSSZ

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

Restoring the old monotonic timer resets its activation origin; rollback therefore restores the old scheduling behavior, not the new persistent catch-up guarantee. Verify its next deadline and do not claim the scheduler is fixed after rollback.
