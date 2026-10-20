# Hostinger PR #20 — controlled installation, stage 1

## Current status

- PR [#20](https://github.com/hailbagel/job-tracker-public/pull/20) merged into `main` at merge commit `fb2f03199c49b419c2515ef614235583a5820725`.
- Ubuntu/Linux CI tests passed on the approved PR head before merge.
- Owner approved **six-hour backoff** for failed attempts, **48-hour minimum** between successful publisher runs, and **one catch-up** after verification of the latest successful systemd service invocation.
- GitHub merge is **not** an installation on Hostinger. The existing VPS timer remains in place until the operator deliberately switches it.
- The last observed successful service completion was `2026-10-15T13:47:18Z` in the available journal evidence. **This is not a permanent assumption:** recheck for any later no-change success before initializing the new state.

## Operator: do this step NOW

Paste the **entire single line** into the normal Hostinger root shell and press Enter:

```bash
cd /opt/vutrulabs/job-tracker-public && test "$(id -u)" -eq 0 && test "$(git branch --show-current)" = main && test -z "$(git status --porcelain=v1 --untracked-files=all)" && ! systemctl is-active --quiet vutrulabs-job-tracker-public.service && printf '\n=== HOST GIT ===\n' && git log -1 --oneline && printf '\n=== TIMER ===\n' && systemctl list-timers --all --no-pager vutrulabs-job-tracker-public.timer && printf '\n=== SERVICE ===\n' && systemctl show vutrulabs-job-tracker-public.service -p Type -p Restart -p WorkingDirectory -p ExecStart -p StateDirectory -p ExecCondition -p ExecStopPost -p ActiveState --no-pager && printf '\n=== CLOCK ===\n' && timedatectl show -p NTPSynchronized && printf '\n=== RECENT SERVICE RESULTS ===\n' && (journalctl -u vutrulabs-job-tracker-public.service --since '2026-10-15 00:00:00' -o short-iso --no-pager | grep -E 'Publication committed and pushed|Publication validated with no public changes|No public dataset or feed changes|PUBLICATION FAILED|Deactivated successfully|Finished|Failed|Started|Starting' || true)
```

This is read-only. It does **not** change the checkout, copy or remove any files, restart a timer, invoke the publisher, or touch `data/`. It aborts early if:
- not running as root;
- not on local `main`;
- there are local modified/untracked files;
- the publisher service is active.

### Return for verification

Send the terminal output (or screenshots) with the `HOST GIT`, `TIMER`, `SERVICE`, `CLOCK` and `RECENT SERVICE RESULTS` sections. Redact confidential values if they appear.

**Do not `git pull`, merge anything, restart the timer or run a production publisher yet.** The next step will be a **root-only backup of the current timer/units**, followed by stopping the timer and performing the reviewed stages in [HOSTINGER_PR20_SCHEDULER_RUNBOOK.md](HOSTINGER_PR20_SCHEDULER_RUNBOOK.md). Do not skip checkpoints. The operator approval already exists; output review still protects against accidentally overwriting new state or executing a stale catch-up.

## Full sequence after successful stage 1

1. Backup current systemd timer, existing service drop-ins and state.
2. Stop old timer (publisher must remain inactive).
3. Fast-forward the Hostinger checkout to the merged GitHub `main`.
4. Install the versioned calendar timer + additive scheduler drop-in.
5. Initialize durable last-success state using verified journal evidence, unless a newer successful run appears.
6. Run systemd/eligibility dry checks, then reload and enable the new timer.
7. Verify the first permitted catch-up publication and re-run the read-only data quality audit.

Each changing stage requires its own inspected output; do not execute stages 2–7 in one unreviewable pasted block.
