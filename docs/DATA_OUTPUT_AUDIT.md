# Read-only public data audit

## Purpose

Validate **all Git-tracked public output under `data/`** without modifying datasets, running collectors, touching the scheduler or writing private runtime material.

The auditor checks:
- enabled automated registry sources vs. `data/source_status.json`;
- the six normalized output file headers per successful source;
- unique source-qualified IDs and URLs; current/detail parity;
- active/inactive history consistency, timestamps and change-event types;
- exact department/location summaries (the `TOTAL` row is **not** an additional group);
- acquisition metadata and recorded counts;
- nonempty descriptions and forbidden `APPLY NOW` placeholders;
- Patrick and SpaceX JSON/CSV ranking counts and ordered IDs;
- parseability of the older public files for failed sources, clearly labeled **stale**;
- extra legacy `jobs_structured.csv` is not assumed to be authoritative.

## Execution

Run from the existing Hostinger checkout, **as a separate read-only command**, only after this script has been merged into `main`:

```bash
cd /opt/vutrulabs/job-tracker-public && git switch main && git pull --ff-only origin main && python3 scripts/audit_data.py
```

Do not combine this with the production publisher. This does **not** start systemd or make a Git commit. It scans locally tracked files and prints `CHECKED`, `INFO`, `WARN`, `FAIL`, then `AUDIT_RESULT FAIL=N WARN=N CHECKED_FILES=N`.

- `FAIL` means a violated data contract, nonzero exit status, or unparseable file.
- `WARN` means degraded completeness/quality (including failed Tesla and Jacobs and blank descriptions).
- `INFO` marks preserved historical/legacy datasets.
- `CHECKED` means that source/feed was inspected, **not** that it passed every check. Review the final counts and detailed messages.

The last known publication commit before this audit was `f78e670` (2026-10-13). Initial targeted inspections found:
- HyImpulse 22 current jobs / 22 detail rows, actual titles and populated descriptions.
- Rocket Factory Augsburg 52 current jobs / 52 detail rows, 10 inactive historical records.
- Exolaunch 11 jobs / 11 detail rows, but **9 detail records with all description fields blank**.
- NEURA 204 current normalized jobs vs. 181 rows in a legacy `jobs_structured.csv` (not proof of a defect by itself).
- Tesla returned HTTP 403 and Jacobs collection failed; preserved historical data must never be labeled current.
- Patrick multi-source feed headline reports 2,826 scanned jobs (2,741 SpaceX + 52 RFA + 11 Exolaunch + 22 HyImpulse).

## Release gate

Do **not** mark the complete `data/` output as verified until a real run of this audit reports its findings and the significant `FAIL` results have been resolved. Do not delete or rewrite historical data to make the audit green. Preserve failed-source status and private/profile boundary.
