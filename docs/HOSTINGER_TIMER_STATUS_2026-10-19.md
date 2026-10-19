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

## Interpretation

- Confirmed successful scheduled collection requires service journal evidence for the requested date plus successful provider status and publication/no-change outcome.
- Latest GitHub dataset snapshots prove successful publication **only through 15 October**.
- Never claim all registered companies are actively tracked: existing providers are 7 automated, of which 5 reported success on the last published run, while new industrial sources are manually registered.
- If a failure exists, correct root cause with a reviewed GitHub change and a separately approved deployment; do not rerun a potentially failing scheduled service blindly.
