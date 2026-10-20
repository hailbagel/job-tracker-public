# Hostinger PR #20 — Read-only service preflight

## Purpose

Inspect the actual Hostinger systemd version, effective Job Tracker service properties and NTP synchronization **before** evaluating the proposed restart-safe scheduler in [PR #20](https://github.com/hailbagel/job-tracker-public/pull/20).

**No installation, publication, timer restart, service start, Git mutation, or data writes.** The existing timer remains unchanged.

## One command to copy into Hostinger

Open the Hostinger VPS terminal and wait for its normal `root@...#` prompt. Copy the **entire single line** below and press Enter:

```bash
systemd --version | head -1 && systemctl show vutrulabs-job-tracker-public.service -p Type -p User -p Group -p ExecStart -p Restart -p ActiveState --no-pager && timedatectl show -p NTPSynchronized --no-pager
```

## What to check in the output

- The installed systemd version is compatible with `ExecCondition` and the proposed calendar timer.
- The service's effective `Type`, `User`, `Group`, `ExecStart`, `Restart`, and `ActiveState` match the intended production contract.
- `NTPSynchronized=yes` confirms time synchronization at the moment of inspection. If `no`, stop and investigate before approving a wall-clock-based scheduler.
- Return the non-sensitive terminal output for review. Do **not** merge PR #20 or deploy to Hostinger on the basis of this read-only preflight alone.

## Approval gate

Even if this check passes, PR #20 needs review of initial scheduler state, the proposed six-hour retry backoff, actual Hostinger unit/drop-ins and deployment/rollback behavior before production approval.
