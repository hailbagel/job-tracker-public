# Hostinger: Read-only full data audit

Repository: `hailbagel/job-tracker-public`

The versioned audit script is `scripts/audit_public_data.py`. It reads the published `data/` outputs without collecting jobs, modifying datasets, starting systemd services, or changing schedules. It checks the registered providers, current/detail/history/change files, summary totals, publication metadata, ranking JSON/CSV/Markdown parity, and tracked-file allowlist.

## Run exactly once

Open a **new** Hostinger VPS root shell. Make sure the normal `root@...#` prompt is visible (not the `>` continuation prompt). Copy and execute this **one line**:

```bash
cd /opt/vutrulabs/job-tracker-public && git switch main && test -z "$(git status --porcelain=v1 --untracked-files=all)" && git pull --ff-only origin main && python3 scripts/audit_public_data.py
```

This only reads data and outputs an audit report to the terminal; it does **not** run the production collector.

## Acceptance

- `=== AUDIT COMPLETE: 0 failures / ... warnings ===`: structural checks passed with clearly identified quality/staleness warnings.
- `[FAIL]` entries or a nonzero exit status: audit failed; **do not modify or delete production datasets**.
- `[WARN]` entries: investigate separately, without misrepresenting stale provider data as current.
- The known Exolaunch missing description fields and Tesla/Jacobs failed acquisitions must remain visible as warnings, not be silently treated as passing coverage.

Return the non-secret terminal report for final assessment. Never paste private profile contents, tokens, environment secrets, SSH credentials or raw crawler captures.

## Current scope and limitation

This audit evaluates the current versioned dataset files and their internal consistency; it does not independently prove that upstream sites list no additional vacancies, that all job descriptions are accurate, or that every hiring source is accessible. File-format validity and content completeness are separate checks.
