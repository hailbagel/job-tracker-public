# Hostinger scheduled publication status — 19 October 2026

## Evidence so far

- Last independently verified GitHub `main` dataset publication: **2026-10-15 13:47:08 UTC** / **15:47:08 CEST**, commit `a8ba2fc494d3c6faecf50571e95b472116dbe6a0`.
- The previous known publication was 2026-10-13 13:46:02 UTC, making a scheduled 48-hour run plausible.
- No more recent published commit or fresher acquisition timestamps were visible at the time of this check (19 October 2026, around 05:56 CEST).
- **This does not prove a timer failure.** The job may not have fired, may have failed, or may have finished without a new commit. Server logs and timer status are necessary to distinguish the cases.
- Four new registry entries (SMS group, Midrex, Mesabi Metallics, Siemens AG) are currently `manual_discovery` and not live collection providers.

## Read-only one-line Hostinger check

Open an existing or new Hostinger root shell at the normal `root@...#` prompt. Copy this **single line**, paste once, and press Enter:

```bash
cd /opt/vutrulabs/job-tracker-public && systemctl is-enabled vutrulabs-job-tracker-public.timer && systemctl list-timers --all --no-pager vutrulabs-job-tracker-public.timer && systemctl show vutrulabs-job-tracker-public.service -p ActiveState -p Result -p ExecMainStatus -p ExecMainStartTimestamp -p ExecMainExitTimestamp --no-pager && journalctl -u vutrulabs-job-tracker-public.service --since '2026-10-15 00:00:00' -n 80 --no-pager -o short-iso && git log -4 --date=iso --pretty=format:'%h %ad %s'
```

This reads systemd timer state, the last recorded service result, journal entries since October 15 and the local Git history. It **does not** start jobs, restart services, modify timers, run the scraper, or edit `data/`.

Return the output with secrets/redacted private information. Inspect especially:

- `list-timers` NEXT and LAST fields.
- `ExecMainStatus=0` and `Result=success` (only refer to the last recorded invocation; need log correlation).
- The log timestamps for October 17 and October 19, including `PUBLICATION FAILED:`, `No public dataset or feed changes`, `Publication committed and pushed` or collection errors.
- If `journalctl` is too short because of the last-80-line limit, expand around the suspected failing day after the first check; do not execute another production run as a diagnostic.

## Follow-up findings from 19 October Hostinger screenshots

The user's actual terminal output shows:

- Timer `vutrulabs-job-tracker-public.timer`: **NEXT 2026-10-21 02:52:19 UTC** (04:52:19 CEST); **LAST = -** and **PASSED = -**.
- Systemd service: `Result=success`, `ExecMainStatus=0`, but `ExecMainStartTimestamp` and `ExecMainExitTimestamp` are blank in the current `systemctl show` result. These properties alone cannot date the successful run.
- The visible journal output ends at **2026-10-15 13:47:18 UTC**, with `Publication committed and pushed`, `Deactivated successfully`, `Finished`.
- No October 17/19 service runs appear among the latest journal entries. The journal command had a latest-80-lines limit, so this is a strong clue rather than exhaustive proof of journal retention.
- **Do not infer a specific root cause yet.** `LAST=-` can be explained by resetting/recreating the timer unit, a reboot with a monotonic timer, or a never-triggered timer. Need actual timer unit configuration plus boot/activation times before recommending edits.

### Focused read-only diagnostic — next action

Copy this **one line** into the normal Hostinger root shell (not a `>` continuation prompt):

```bash
cd /opt/vutrulabs/job-tracker-public && printf '\n=== TIMER UNIT ===\n' && systemctl cat vutrulabs-job-tracker-public.timer && printf '\n=== TIMER STATUS ===\n' && systemctl status vutrulabs-job-tracker-public.timer --no-pager -l && printf '\n=== TIMER SETTINGS ===\n' && systemctl show vutrulabs-job-tracker-public.timer -p ActiveEnterTimestamp -p LastTriggerUSec -p NextElapseUSecRealtime -p NextElapseUSecMonotonic -p Unit -p Persistent --no-pager && printf '\n=== BOOT ===\n' && uptime -s && printf '\n=== TIMER JOURNAL ===\n' && journalctl -u vutrulabs-job-tracker-public.timer --since '2026-10-15 00:00:00' -n 50 --no-pager -o short-iso && printf '\n=== SERVICE JOURNAL SINCE OCT 16 ===\n' && journalctl -u vutrulabs-job-tracker-public.service --since '2026-10-16 00:00:00' -n 70 --no-pager -o short-iso
```

The command reads the timer definition, activation state, last trigger, calculated next trigger, boot time, and **only logs since October 16** for the timer and service. It changes nothing, creates no jobs, and does not touch `data/`.

Interpret alongside `systemctl cat`: if the timer uses `OnBootSec`, `OnActiveSec` or `OnUnitActiveSec` without a persistent calendar schedule, reboot/restart may defer the next run. **Persistent=true does not retroactively catch up monotonic elapsed timers; inspect the real unit first.** An `OnCalendar` with `Persistent=true` and a separately validated schedule may be preferable, but no write or reload should occur until diagnosis and owner approval.

A 48-hour interval and a twice-daily schedule are distinct requirements; keep the existing cadence unless the owner asks to change it. No manual publication should be started merely because a timer trigger is missing.

## Interpretation

- Confirmed successful scheduled collection requires service journal evidence for the requested date plus successful provider status and publication/no-change outcome.
- Latest GitHub dataset snapshots prove successful publication **only through 15 October**.
- Never claim all registered companies are actively tracked: existing providers are 7 automated, of which 5 reported success on the last published run, while new industrial sources are manually registered.
- If a failure exists, correct root cause with a reviewed GitHub change and a separately approved deployment; do not rerun a potentially failing scheduled service blindly.
