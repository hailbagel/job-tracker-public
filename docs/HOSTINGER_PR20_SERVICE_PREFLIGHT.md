# Hostinger PR #20 — Read-only service preflight

## Purpose

Inspect the actual Hostinger systemd version, effective Job Tracker service properties and NTP synchronization **before** evaluating the proposed restart-safe scheduler in [PR #20](https://github.com/hailbagel/job-tracker-public/pull/20).

**No installation, publication, timer restart, service start, Git mutation, or data writes.** The existing timer remains unchanged.

## One command to copy into Hostinger

Open the Hostinger VPS terminal and wait for its normal `root@...#` prompt. Copy the **entire single line** below and press Enter:

```bash
systemd --version | head -1 && systemctl show vutrulabs-job-tracker-public.service -p Type -p User -p Group -p ExecStart -p Restart -p ActiveState --no-pager && timedatectl show -p NTPSynchronized
```

## What to check in the output

- The installed systemd version is compatible with `ExecCondition` and the proposed calendar timer.
- The service's effective `Type`, `User`, `Group`, `ExecStart`, `Restart`, and `ActiveState` match the intended production contract.
- `NTPSynchronized=yes` confirms time synchronization at the moment of inspection. If `no`, stop and investigate before approving a wall-clock-based scheduler.
- Return the non-sensitive terminal output for review. Do **not** merge PR #20 or deploy to Hostinger on the basis of this read-only preflight alone.

## Approval gate

Even if this check passes, PR #20 needs review of initial scheduler state, the proposed six-hour retry backoff, actual Hostinger unit/drop-ins and deployment/rollback behavior before production approval.

## Actual Hostinger preflight result — 20 October 2026

User-supplied terminal screenshot confirmed:

| Property | Observed | Assessment |
|---|---|---|
| `systemd` | `255 (255.4-1ubuntu8.18)` | Compatible with `ExecCondition` |
| `Type` | `oneshot` | Appropriate for the bounded publisher |
| `Restart` | `no` | Does not independently restart the publisher |
| `ExecStart` | Python from `/opt/vutrulabs/job-tracker-public/.venv/bin/python` | Program exists; full argv truncated in photo |
| `User` / `Group` | blank | Under systemd defaults, runs as root |
| `ActiveState` | `inactive` | No active production service |
| `NTPSynchronized` | `yes` | NTP synchronization reported on host |

The first terminal try produced a `timedatectl: unrecognized option '--no-pager'` error; repeating without `--no-pager` confirmed `NTPSynchronized=yes`. The copy/paste command above should be updated to avoid adding `--no-pager` to `timedatectl`.

**Outcome:** Host environment fundamentals confirmed; a screenshot of truncated `ExecStart` is not proof of the entire service definition. No rollout is authorized by this check. PR #20 remains a draft pending production-service and bootstrap policy review.

## Optional final read-only service check before deployment approval

Use **this exact single line** in the normal Hostinger shell (never paste an extra shell block):

```bash
systemctl show vutrulabs-job-tracker-public.service -p Type -p ExecStart -p WorkingDirectory -p ExecCondition -p ExecStartPost -p ExecStopPost -p StateDirectory -p User -p Group -p ActiveState --no-pager && systemctl cat vutrulabs-job-tracker-public.timer
```

This displays effective service command and proposed hook presence (without starting anything), and the current timer file. Redact any secrets in the terminal output if additional confidential configuration is displayed. Verify the real `ExecStart` is the approved publisher invocation and all scheduler hooks (`ExecCondition`, `ExecStartPost`, `ExecStopPost`) are presently absent before installing the new drop-in. If any are already configured, stop; do not overwrite them.

**Deployment policy:** after this read-only inspection, explicitly approve the six-hour failed-attempt retry policy, initial last-success timestamp / safe first-run anchor and whether overdue catch-up may run on activation; then review/merge PR #20, and only afterward perform a controlled Hostinger installation with backup and rollback, followed by unattended acceptance.
