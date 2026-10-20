# PR #20 — Hostinger deployment stage 3: synchronize approved code

## Confirmed prerequisite

From Hostinger terminal screenshot (20 October 2026):

- Old timer backup: `/root/vutrulabs-scheduler-backup-20261020T104026Z`
- The operator saw `ActiveState=inactive`, `SubState=dead` for the timer **and** publisher service.
- GitHub PR #20 was merged into `main`, merge commit `fb2f03199c49b419c2515ef614235583a5820725`.
- This document is part of the versioned operations runbook. **Do not confuse a code update with installing or enabling the scheduler.**

## Exactly ONE line to run in Hostinger

Copy this entire line at the normal root terminal prompt and press Enter:

```bash
bash -lc 'set -euo pipefail; cd /opt/vutrulabs/job-tracker-public; test "$(id -u)" -eq 0; test "$(git branch --show-current)" = main; test -f /root/vutrulabs-scheduler-backup-20261020T104026Z/vutrulabs-job-tracker-public.timer; test -z "$(git status --porcelain=v1 --untracked-files=all)"; if systemctl is-active --quiet vutrulabs-job-tracker-public.timer || systemctl is-active --quiet vutrulabs-job-tracker-public.service; then echo "STOP: timer or publisher is active"; exit 1; fi; git fetch origin main; git pull --ff-only origin main; git merge-base --is-ancestor fb2f03199c49b419c2515ef614235583a5820725 HEAD; test -f scripts/hostinger_scheduler_state.py; test -f scripts/check_hostinger_scheduler.py; test -f scripts/systemd/vutrulabs-job-tracker-public.timer; test -f scripts/systemd/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf; printf "\n=== CODE UPDATED, TIMER STILL STOPPED ===\n"; git log -1 --oneline; git status --short --branch; systemctl show vutrulabs-job-tracker-public.timer -p ActiveState -p SubState --no-pager; systemctl show vutrulabs-job-tracker-public.service -p ActiveState -p SubState --no-pager'
```

## Effects and safeguards

1. Requires root, local `main`, verified old timer backup and a **clean** Git worktree.
2. Aborts if old timer or publisher service is active.
3. Fetches the latest `main` from GitHub and fast-forwards only (no force push, reset, stash, or branch switch).
4. Confirms merge commit `fb2f03199c49b419c2515ef614235583a5820725` is an ancestor of the checkout, then verifies the four required scheduler files exist.
5. Prints current commit and both systemd unit states. **Does not install, start, restart, or enable services; does not run collection or alter data.**

## Acceptance

Only continue after the command finishes successfully, `git status --short --branch` reports a clean `main`, and both units remain `inactive`. If the command stops anywhere, report the error and **do not** start the old timer or run the publisher.

The next separately approved stage is installing the new calendar timer, the service drop-in and the initial durable state; those steps require independent checks and must not be combined into this command.

Full reviewed deploy/rollback sequence: [HOSTINGER_PR20_SCHEDULER_RUNBOOK.md](HOSTINGER_PR20_SCHEDULER_RUNBOOK.md).
