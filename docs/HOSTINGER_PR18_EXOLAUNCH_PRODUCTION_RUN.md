# Hostinger production acceptance — Exolaunch Personio details, PR #18

Repository: `hailbagel/job-tracker-public`  
Merged change: [PR #18](https://github.com/hailbagel/job-tracker-public/pull/18), merge commit `adf6f94ee58ba755dbe464e43e5b69409d7cdc0c`.

## Why this is needed

The code update enables a generic Personio JobPosting JSON-LD detail-page fallback when a public Personio XML position has no text. The existing October 13 production data were written **before** PR #18: Exolaunch had 11 positions but 9 had empty `mission`, `requirements`, and `benefits`.

Codex review was marked Completed with no review findings published; GitHub reported no completed CI check runs. Production acceptance is still required.

## If you already ran the read-only audit (0 failures / 4 warnings)

A terminal that shows only `=== READ-ONLY DATA AUDIT ===` and `0 failures / 4 warnings` did **not** demonstrate a new collection or publication. The audit does not update jobs.

When you are already at the clean `root@...:/opt/vutrulabs/job-tracker-public#` prompt and have **not yet started a production run after PR #18**, use **only** this command, not the audit-only command:

```bash
python3 scripts/run_hostinger_pr15.py
```

It should print `RUNNING: versioned Hostinger PR15 single-run procedure`, then `=== PRECHECK SERVICE ===` and later `=== START ONE PRODUCTION RUN THROUGH SYSTEMD ===`. Wait for the command to finish. If it fails, do **not** rerun or start the service manually; capture non-secret output for review. Only after a confirmed successful publication should you run the separate read-only audit to check Exolaunch detail completeness.

## One controlled production run and read-only audit

Open a **fresh Hostinger root terminal** and ensure the normal `root@...#` prompt is present, not a `>` continuation prompt. Paste exactly this **one line** and press Enter:

```bash
cd /opt/vutrulabs/job-tracker-public && test -z "$(git status --porcelain=v1 --untracked-files=all)" && git switch main && git pull --ff-only origin main && python3 scripts/run_hostinger_pr15.py && python3 scripts/audit_public_data.py
```

Why reuse `scripts/run_hostinger_pr15.py`: this is the already used and verified one-shot systemd production wrapper. It loads the versioned full Hostinger runbook, verifies service/timer/Git, performs **one** publication, checks the output/push, and does not change the scheduler. The name refers to the original runbook, not to a restriction on later source-code fixes.

**Do not execute twice.** If any step fails, stop and return the non-secret terminal output. No force-pushes, resets, direct dataset edits or unattended retries.

## Required acceptance

- Systemd publication `Result=success` and `ExecMainStatus=0`.
- `main` matches `origin/main`; successful non-force push or documented no-change behavior.
- HyImpulse remains `personio_xml`, with correct job titles and no broken detail rows.
- Exolaunch has equal positive `jobs_latest.csv` and `job_details.csv` counts; **all current Exolaunch jobs have at least one non-empty detail text field**.
- The read-only data audit ends with **0 failures** and **no Exolaunch blank-description warning**. Other known warnings (stale Tesla/Jacobs data and NEURA auxiliary discrepancy) are separate blockers and must remain visible.
- `data/source_status.json` reflects the latest Exolaunch acquisition and the Patrick Space/Rocket feed includes Exolaunch as a successfully published contributor.
- Verify the next scheduled timer activation remains present.

The audit checks data contract consistency, **not independently complete live upstream vacancy coverage**.

## Interpretation

If Exolaunch still reports `9/11 details lack all description fields` or another missing-detail count, the intended detail fallback did not produce the expected live output. Record the upstream failure and return to the code review; do not claim successful release merely because the systemd service was invoked.

The next normal 48-hour scheduled run also requires independent observation before the pipeline can be called *unattended production verified*.