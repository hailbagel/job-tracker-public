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

## Git workflow

Create a **feature branch + PR** for the reviewed timer repair design and tests. Keep all prompts, units and operating decisions committed. Do not merge/deploy before owner approval. Link the eventual acceptance evidence (journal, service result, fresh data timestamp) in a follow-up documentation commit.
