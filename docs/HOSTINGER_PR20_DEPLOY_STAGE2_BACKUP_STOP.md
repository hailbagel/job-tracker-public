# PR20 Hostinger deployment — stage 2: back up and stop OLD timer

**Owner authorization:** Explicit approval for PR #20 merge, six-hour failure cooldown, catch-up after journal-verification and controlled Hostinger installation with backup and rollback. GitHub PR #20 is already merged at `fb2f031`. Current VPS is not yet updated.

## Operator: run exactly ONE line

At the normal root shell on Hostinger, copy this entire command and press Enter:

```bash
bash -lc 'set -euo pipefail; test "$(id -u)" -eq 0; cd /opt/vutrulabs/job-tracker-public; test "$(git branch --show-current)" = main; test -z "$(git status --porcelain=v1 --untracked-files=all)"; if systemctl is-active --quiet vutrulabs-job-tracker-public.service; then echo "STOP: publisher still running"; exit 1; fi; TIMER=/etc/systemd/system/vutrulabs-job-tracker-public.timer; DROPIN=/etc/systemd/system/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf; STATE=/var/lib/vutrulabs-job-tracker-public/state.json; BACKUP=/root/vutrulabs-scheduler-backup-$(date -u +%Y%m%dT%H%M%SZ); test -f "$TIMER"; test ! -e "$BACKUP"; install -d -m 0700 "$BACKUP"; cp -a "$TIMER" "$BACKUP/vutrulabs-job-tracker-public.timer"; if test -e "$DROPIN"; then cp -a "$DROPIN" "$BACKUP/20-scheduler-gate.conf"; else touch "$BACKUP/dropin-was-absent"; fi; if test -e "$STATE"; then cp -a "$STATE" "$BACKUP/state.json"; else touch "$BACKUP/state-was-absent"; fi; systemctl is-enabled vutrulabs-job-tracker-public.timer > "$BACKUP/timer-enabled" 2>&1 || true; systemctl is-active vutrulabs-job-tracker-public.timer > "$BACKUP/timer-active" 2>&1 || true; systemctl stop vutrulabs-job-tracker-public.timer; printf "BACKUP=%s\n" "$BACKUP"; systemctl show vutrulabs-job-tracker-public.timer -p ActiveState -p SubState --no-pager; systemctl show vutrulabs-job-tracker-public.service -p ActiveState -p SubState --no-pager'
```

### What this does
- Aborts if not root, not on clean local `main`, or the publisher service is currently running.
- Creates a unique root-only backup directory `/root/vutrulabs-scheduler-backup-<UTC timestamp>`.
- Saves a copy of the old timer and any existing PR20 drop-in / state file, or writes markers if absent.
- Records whether the timer was enabled/active.
- **Stops only the timer**, NOT an active publisher service.
- Prints `BACKUP=...` and the final timer/service status.

### Expected result / acceptance

`ActiveState=inactive` for the timer; the service also remains `inactive`. Preserve the **actual BACKUP path** shown in terminal. Do not commit the private root backup to Git, delete state, reboot Hostinger, start a new collection, or pull changes until this stage has been checked.

If any check aborts, **stop and share the error**. Do not try another command. If it stops the timer but the service is active, wait for the running publisher to finish and inspect its journal before proceeding.

### Next stages after review

Stage 3: fast-forward clean Hostinger `main`, stage 4: install reviewed timer and drop-in, stage 5: initialize state from the latest verified successful invocation (recheck if a new one occurred), stage 6: static validation and gated timer activation, stage 7: capture actual unattended catch-up run evidence. The complete approved architecture and rollback procedures are in [HOSTINGER_PR20_SCHEDULER_RUNBOOK.md](HOSTINGER_PR20_SCHEDULER_RUNBOOK.md). Keep each stage separate.
