# Copilot — final code review before Hostinger scheduler PR #20 is merged

Target: [PR #20 — restart-safe Hostinger scheduler](https://github.com/hailbagel/job-tracker-public/pull/20) on branch `fix/hostinger-restart-safe-scheduler`. Repo: `hailbagel/job-tracker-public`.

## Verified evidence

- Host Ubuntu 24.04 runs systemd 255, effective service `Type=oneshot`, `Restart=no`, default root user, inactive service, and `WorkingDirectory=/opt/vutrulabs/job-tracker-public`.
- Current service runs a venv Python command at `/opt/vutrulabs/job-tracker-public/.venv/bin/python`; full `ExecStart` arguments are cut off in the screenshot.
- Old timer is `OnActiveSec=48h` + `OnUnitInactiveSec=48h`; the new calendar/eligibility service drop-in is **not installed**. No `StateDirectory` or scheduler hooks shown.
- `NTPSynchronized=yes` observed in earlier preflight.
- GitHub Actions Linux CI [run 39276526770](https://github.com/hailbagel/job-tracker-public/actions/runs/39276526770) passed all steps including all Python tests and synthetic oneshot unit verification.
- Full preflight transcript interpretation is in [HOSTINGER_PR20_SERVICE_PREFLIGHT.md](HOSTINGER_PR20_SERVICE_PREFLIGHT.md).
- Latest verified public data publication remains 2026-10-15 at 13:47:08 UTC; later no-change publisher runs are not ruled out by the Git commit record.

## Final review duties — code and operations

1. Compare `scripts/systemd/vutrulabs-job-tracker-public.timer`, `scripts/systemd/vutrulabs-job-tracker-public.service.d/20-scheduler-gate.conf`, `scripts/hostinger_scheduler_state.py`, `scripts/check_hostinger_scheduler.py` and all tests in PR #20 against systemd service semantics for `Type=oneshot`.
2. Specifically confirm `ExecCondition` runs at expected skip/error statuses, environment variables `INVOCATION_ID` and `SERVICE_RESULT` in `ExecStopPost`, `ExecStartPost` successful completion ordering, and whether `ExecStopPost` gets called for skipped condition. Check failure cases: publisher exit nonzero, success-state write fails, aborted/crashed publisher, reboot during run, and missing/corrupt state. A superficial synthetic syntax check alone does **not** prove this behavior.
3. Verify `StateDirectory=` path permissions, state file atomicity, boot and UTC clock adjustments, and that no duplicate publisher run can occur under service/timer + manually invoked legacy publisher lock.
4. Check the documented six-hour failed-attempt cooldown and 48-hour minimum-since-success behavior across missed hours and restarts; explicit owner approval for deployment remains required.
5. Check bootstrap design **without inventing last success**: do not assume latest published Git commit proves latest completed invocation, as a no-change run can succeed with no new commit. If the actual latest success cannot be proven, prepare conservative `first_run_after_utc` policy and advise consequences for stale jobs.
6. Prepare a **single versioned Hostinger operator runbook** with exact, staged **separate** copy/paste commands for: read-only effective unit/argv and host readiness, backups, branch synchronization and file installation, state initialization, unit verification, daemon reload/activation, dry checks, and rollback. Never jam all operations into one unreviewable paste; include explicit decision checkpoints.
7. Ensure no Hostinger command is run and no secrets/private data are stored or printed in the public repository. No direct `git reset`, force-push, or direct mutation of the public `data/` output snapshots.
8. If significant issues are found, add targeted tests/fixes to the PR feature branch and report failures. Do not merge/deploy until tests and review pass. If no blocker is found, produce a concise risk summary and precisely identify the still-required owner approvals: six-hour retry cooldown, initial bootstrap anchor, immediate catch-up or deliberate wait, merge and deployment.

## Deliverable

Review findings (with severity, exact file/line, justification), reproducible test commands/results and versioned deployment/rollback artifacts. Keep changes on the PR branch for review. **Do not merge PR #20 or change the Hostinger installation without the owner's explicit approval.**
