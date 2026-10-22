# PAPERCLIP TASK – Hostinger-Frischemonitor für 6-h-Takt

**STATUS:** NACH F1, CTO. **Ziel:** Paperclip → VuTruLabs → New Task. Jeden der folgenden vier Codeblöcke **einzeln** in das zugehörige Feld kopieren. **Nicht** in VS Copilot. Noch kein Paperclip-Task durch diese Repo-Datei angelegt.

## Title
```text
JT-SCHEDULER-MONITOR – Align alerts with six-hour schedule
```

## Assignee
```text
CTO
```

## Project
```text
Job Tracker Public
```

## Prompt
```text
Role: CTO engineering agent, VuTruLabs Paperclip.
Task: JT-SCHEDULER-MONITOR – correct six-hour scheduler freshness monitoring.
Repo: https://github.com/hailbagel/job-tracker-public
Issue: https://github.com/hailbagel/job-tracker-public/issues/28

Evidence: scripts/hostinger_scheduler_state.py MINIMUM_INTERVAL=RETRY_INTERVAL=6h; scripts/check_hostinger_scheduler.py uses STALE_AFTER=60h and returns success while last_success is under 60h. This hides missed six-hour cycles. Do NOT redesign or silently change the production six-hour scheduler.

1. Start only after CTO has finished/paused F1, or in a separately isolated safe worktree. Inspect current main and PRs. No duplicate branch, reset, stash or forced pushes.
2. Make the read-only health check genuinely cadence-aware using durable state, expected eligibility deadline, last attempt status, effective timer/service state and explicitly justified configurable grace. Distinguish successful skipped hourly checks, six-hour eligibility, in-progress, first-run bootstrap, cooldown after failure, missed success, timer disabled, malformed/future timestamps and clock drift.
3. Return actionable WARN and nonzero CRITICAL/FAIL for overdue runs or actual failures, including when last success age is below 60h. Do not treat skipped eligibility checks or unchanged output data as failed production runs.
4. Add deterministic mocked-timestamp and systemd-property tests for normal six-hour operation, several missed cycles, failed last attempt after prior success, last_success future, missing state, reboot/persistent state and disabled timer; verify actual exit codes.
5. Keep checker read-only, secrets private, no SSH/write actions, no production publish and no systemd restart, enable, daemon-reload, schedule or cadence change.
6. Produce new isolated feature branch and ONE draft PR referencing Issue #28; focused tests, full applicable suite, Ubuntu CI, git diff --check. No merge/deploy.
7. Post PR/commit links, evidence for chosen grace/thresholds and host-only verification command for later operator review (read-only); cite conditions that require a separate deploy/rollback decision.

Done: code+tests+draft PR, monitoring can detect missed six-hour production cycles, no production changes.
```

---

Kein autonomes Mergen, Hostinger-Deployment oder Zugriff auf private Bewerberdaten. PR/Tests/Status im Paperclip-Task dokumentieren.
