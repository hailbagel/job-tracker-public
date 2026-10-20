# Hostinger PR20 — Stage 5: verify last success and initialize durable state

## Confirmed before this step

The operator's Stage 4 screenshot (20 Oct 2026) shows:
- The PR20 calendar timer unit and service drop-in are installed exactly from versioned files.
- `/var/lib/vutrulabs-job-tracker-public` exists and has root-only permissions `0700`.
- Timer and publisher service both remain `inactive/dead`; no `daemon-reload` or timer activation has been executed.
- The root-only old-timer backup exists at `/root/vutrulabs-scheduler-backup-20261020T104026Z`.
- GitHub PR #20 was merged; approved policy: 48 hours since last successful publisher completion, 6-hour backoff after failures, and catch-up permitted only when the actual last-success time is verified.

## Copy this ONE line into the normal Hostinger root shell

```bash
bash -lc 'set -euo pipefail; cd /opt/vutrulabs/job-tracker-public; test "$(id -u)" -eq 0; test "$(git branch --show-current)" = main; test -z "$(git status --porcelain=v1 --untracked-files=all)"; test -f /root/vutrulabs-scheduler-backup-20261020T104026Z/vutrulabs-job-tracker-public.timer; test -f /etc/systemd/system/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf; test ! -e /var/lib/vutrulabs-job-tracker-public/state.json; test "$(stat -c %a /var/lib/vutrulabs-job-tracker-public)" = 700; if systemctl is-active --quiet vutrulabs-job-tracker-public.timer || systemctl is-active --quiet vutrulabs-job-tracker-public.service; then echo "STOP: timer or publisher active"; exit 1; fi; PROOF="$(journalctl -u vutrulabs-job-tracker-public.service --since "2026-10-15 13:47:00 UTC" --until "2026-10-15 13:47:20 UTC" -o cat --no-pager)"; case "$PROOF" in *"Publication committed and pushed"*"Finished"*) : ;; *) echo "STOP: successful Oct 15 publication not verifiable"; exit 1;; esac; RECENT="$(journalctl -u vutrulabs-job-tracker-public.service --since "2026-10-15 13:47:19 UTC" -o cat --no-pager)"; if printf "%s\n" "$RECENT" | grep -E "Publication committed and pushed|Publication validated with no public changes|No public dataset or feed changes|Deactivated successfully|Finished vutrulabs-job-tracker-public.service"; then echo "STOP: newer possible success; re-evaluate anchor"; exit 1; fi; /usr/bin/python3 scripts/hostinger_scheduler_state.py initialize --state-file /var/lib/vutrulabs-job-tracker-public/state.json --last-success-utc 2026-10-15T13:47:18Z; printf "\n=== DURABLE STATE INITIALIZED, TIMER STILL STOPPED ===\n"; /usr/bin/python3 -c "import json; from pathlib import Path; d=json.loads(Path(\"/var/lib/vutrulabs-job-tracker-public/state.json\").read_text()); print(\"last_success_utc=\",d[\"last_success_utc\"],\"last_attempt_status=\",d[\"last_attempt_status\"])" ; stat -c "state_mode=%a owner=%U" /var/lib/vutrulabs-job-tracker-public/state.json; /usr/bin/python3 scripts/hostinger_scheduler_state.py eligible --state-file /var/lib/vutrulabs-job-tracker-public/state.json --dry-run; systemctl show vutrulabs-job-tracker-public.timer -p ActiveState -p SubState --no-pager; systemctl show vutrulabs-job-tracker-public.service -p ActiveState -p SubState --no-pager'
```

### Safety, effect and limitations

- Checks root, clean local `main`, the existing backup, the installed drop-in, root-only state directory and both services inactive.
- **Requires positive journal evidence** of the 15 Oct successful publication and finished service, and **aborts on any later possible successful publication** in the available systemd journal. Do not guess the most recent success. These checks work only to the extent that the journal is retained: if records are missing, stop.
- Creates exactly one root-only `/var/lib/vutrulabs-job-tracker-public/state.json` with `last_success_utc=2026-10-15T13:47:18Z`; refuses to overwrite an existing state file.
- Performs a read-only `eligible --dry-run` and displays timer and service states.
- **Does not start the publisher or timer, reload systemd, alter Git, or touch public dataset files**.

### Expected acceptance output

- `[OK] Initialized scheduler state: .../state.json`
- `last_success_utc= 2026-10-15T13:47:18.000000Z` and `last_attempt_status= None`.
- State file `state_mode=600 owner=root`.
- `[OK] Publisher would be eligible; scheduler state was not changed`.
- Timer **and** service remain `ActiveState=inactive`, `SubState=dead`.

If the command stops or prints `STOP`, **do not rerun**. Report the non-secret terminal output so the timestamp can be reconciled safely.

Next stage (not part of this command): `systemd-analyze verify`, calendar checks, actual unit inspection, `daemon-reload` and controlled timer activation, with observation of the approved catch-up. See [HOSTINGER_PR20_SCHEDULER_RUNBOOK.md](HOSTINGER_PR20_SCHEDULER_RUNBOOK.md).
