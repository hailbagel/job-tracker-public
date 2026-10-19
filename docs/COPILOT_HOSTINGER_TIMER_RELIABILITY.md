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

Per `systemd.timer(5)`, `OnActiveSec=` measures time since *timer activation*; `OnUnitInactiveSec=` measures time since the triggered service was last deactivated. Both are monotonic timers. If the timer unit is stopped/restarted, its activation-origin changes. Monotonic timers do not inherently catch up across downtime the same way `OnCalendar=` with `Persistent=true` can. Verify this against the installed systemd version and current systemd state before designing a change.

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
