# Hostinger PR20 — Deployment stage 4: install the versioned unit files (NO activation)

## Prerequisites confirmed on 20 Oct 2026

- Stage 2 created root-only backup at `/root/vutrulabs-scheduler-backup-20261020T104026Z`.
- Stage 3 fast-forwarded local `main` through merge `fb2f031` to `66d0e69` and showed a clean branch.
- Old timer and publisher service were both `inactive / dead`.
- The operator approved a controlled installation with backup and rollback, as well as the 6-hour retry cooldown and an overdue catch-up **only after the last success is revalidated**.

## Copy exactly ONE line into the normal Hostinger root terminal

```bash
bash -lc 'set -euo pipefail; cd /opt/vutrulabs/job-tracker-public; test "$(id -u)" -eq 0; test "$(git branch --show-current)" = main; test -z "$(git status --porcelain=v1 --untracked-files=all)"; test -f /root/vutrulabs-scheduler-backup-20261020T104026Z/vutrulabs-job-tracker-public.timer; test -e /root/vutrulabs-scheduler-backup-20261020T104026Z/dropin-was-absent; test -e /root/vutrulabs-scheduler-backup-20261020T104026Z/state-was-absent; if systemctl is-active --quiet vutrulabs-job-tracker-public.timer || systemctl is-active --quiet vutrulabs-job-tracker-public.service; then echo "STOP: timer or publisher is active"; exit 1; fi; test ! -e /etc/systemd/system/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf; test ! -e /var/lib/vutrulabs-job-tracker-public/state.json; test -f scripts/systemd/vutrulabs-job-tracker-public.timer; test -f scripts/systemd/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf; install -d -m 0755 /etc/systemd/system/vutrulabs-job-tracker-public.service.d; install -d -m 0700 /var/lib/vutrulabs-job-tracker-public; install -m 0644 scripts/systemd/vutrulabs-job-tracker-public.timer /etc/systemd/system/vutrulabs-job-tracker-public.timer; install -m 0644 scripts/systemd/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf /etc/systemd/system/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf; cmp -s scripts/systemd/vutrulabs-job-tracker-public.timer /etc/systemd/system/vutrulabs-job-tracker-public.timer; cmp -s scripts/systemd/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf /etc/systemd/system/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf; printf "\n=== PR20 UNIT FILES INSTALLED, NOT ACTIVATED ===\n"; ls -ld /var/lib/vutrulabs-job-tracker-public; grep -E "^(OnCalendar|Persistent|ExecCondition|ExecStopPost|StateDirectory)=" /etc/systemd/system/vutrulabs-job-tracker-public.timer /etc/systemd/system/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf; systemctl show vutrulabs-job-tracker-public.timer -p ActiveState -p SubState --no-pager; systemctl show vutrulabs-job-tracker-public.service -p ActiveState -p SubState --no-pager'
```

## Effect

This installs only:
- `/etc/systemd/system/vutrulabs-job-tracker-public.timer`
- `/etc/systemd/system/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf`
- An empty, root-only directory `/var/lib/vutrulabs-job-tracker-public` (mode 0700).

It checks the original backup and the absence of a prior scheduler drop-in/state file; aborts if either unit is active; copies the versioned files; confirms exact matches; and displays both existing unit states. This stage **does NOT run `systemctl daemon-reload`, start/enable/restart the timer, execute a scraper, initialize the state, change Git history, or write to public `data/`**.

### Acceptance before any next stage

Expect `=== PR20 UNIT FILES INSTALLED, NOT ACTIVATED ===`, matching `OnCalendar`, `Persistent`, `ExecCondition`, `ExecStopPost`, `StateDirectory`, and both units remaining `ActiveState=inactive`, `SubState=dead`.

If anything fails, **do not rerun**, don't independently activate the service and don't delete the backup. Return the terminal output for diagnosis. If stopped after copying only one file, the old timer must remain stopped until the partial state is assessed.

After operator output review, stage 5 will re-check the actual last successful service invocation and initialize durable `state.json` using the verified timestamp, followed by static unit verification and controlled timer activation. A catch-up is not initiated in this stage.

Full deployment and rollback documentation: [HOSTINGER_PR20_SCHEDULER_RUNBOOK.md](HOSTINGER_PR20_SCHEDULER_RUNBOOK.md).
