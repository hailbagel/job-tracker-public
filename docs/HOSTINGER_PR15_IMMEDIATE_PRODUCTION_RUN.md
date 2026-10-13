# Hostinger Runbook — Immediate Production Publication After PR #15

Use this runbook only after PR #15 has been merged into `main`.

Repository:

```text
hailbagel/job-tracker-public
```

Host checkout:

```text
/opt/vutrulabs/job-tracker-public
```

Systemd service:

```text
vutrulabs-job-tracker-public.service
```

Systemd timer:

```text
vutrulabs-job-tracker-public.timer
```

## Purpose

Run exactly one immediate production publication using the same systemd service/environment as the existing 48-hour scheduler, then verify that the newly merged HyImpulse Personio acquisition produced clean public data and pushed it to GitHub.

This is a human-operated Hostinger step.

Do not paste SSH keys, tokens, private profile contents, or credentials into ChatGPT, Paperclip, GitHub issues, or logs.

Do not alter credentials, SSH configuration, the private Patrick profile, or the scheduler configuration.

---

## Preconditions

Before running:

- PR #15 must be merged to `main`.
- There must be no unresolved P1/P2 review blocker.
- The Hostinger checkout must be the existing root-owned restricted deployment path.
- The production service must not already be running.
- Do not run a second publication if the first attempt fails. Capture evidence and stop.

---

## Single bounded Hostinger command block

The previous version used whitespace-sensitive `grep` checks and stopped before starting the service because the compact JSON registry uses `"id":"hyimpulse"`. This corrected version parses JSON instead. A successful configuration check alone is **not** proof that the publication ran.

Run as root in the Hostinger VPS terminal:

```bash
set -euo pipefail

cd /opt/vutrulabs/job-tracker-public

echo "=== PRECHECK SERVICE ==="
systemctl is-active vutrulabs-job-tracker-public.service || true

if systemctl is-active --quiet vutrulabs-job-tracker-public.service; then
  echo "STOP: publication service is already active"
  exit 90
fi

echo "=== PRECHECK TIMER ==="
systemctl is-enabled vutrulabs-job-tracker-public.timer
TZ=UTC systemctl list-timers --all --no-pager vutrulabs-job-tracker-public.timer

echo "=== PRECHECK GIT ==="
git switch main
git status --short

if [ -n "$(git status --porcelain=v1 --untracked-files=all)" ]; then
  echo "STOP: Hostinger worktree is not clean"
  exit 91
fi

git fetch origin main
git pull --ff-only origin main

LOCAL_BEFORE="$(git rev-parse HEAD)"
REMOTE_BEFORE="$(git rev-parse origin/main)"

echo "local_before=$LOCAL_BEFORE"
echo "remote_before=$REMOTE_BEFORE"

if [ "$LOCAL_BEFORE" != "$REMOTE_BEFORE" ]; then
  echo "STOP: local main does not match origin/main"
  exit 92
fi

echo "=== VERIFY PR15 CODE PRESENT ==="
python3 - <<'PY'
import json
from pathlib import Path

registry = json.loads(Path("configs/sources.json").read_text(encoding="utf-8"))
hyimpulse = next(source for source in registry["sources"] if source["id"] == "hyimpulse")
print("hyimpulse_adapter=", hyimpulse.get("adapter"))
print("hyimpulse_mode=", hyimpulse.get("acquisition_mode"))
if hyimpulse.get("adapter") != "personio_xml" or hyimpulse.get("acquisition_mode") != "api":
    raise SystemExit("STOP: HyImpulse Personio XML configuration is not deployed")
print("HYIMPULSE CONFIG OK")
PY

echo "=== START ONE PRODUCTION RUN THROUGH SYSTEMD ==="
set +e
systemctl start vutrulabs-job-tracker-public.service
START_RC=$?
set -e

echo "systemctl_start_rc=$START_RC"

echo "=== SERVICE RESULT ==="
systemctl show vutrulabs-job-tracker-public.service   -p Result   -p ExecMainStatus   -p ExecMainStartTimestamp   -p ExecMainExitTimestamp   --no-pager

if [ "$START_RC" -ne 0 ]; then
  echo "=== FAILURE LOG ==="
  journalctl -u vutrulabs-job-tracker-public.service -n 120 --no-pager
  echo "STOP: production publication failed - DO NOT RETRY"
  exit "$START_RC"
fi

RESULT="$(systemctl show vutrulabs-job-tracker-public.service -p Result --value)"
STATUS="$(systemctl show vutrulabs-job-tracker-public.service -p ExecMainStatus --value)"

if [ "$RESULT" != "success" ] || [ "$STATUS" != "0" ]; then
  echo "=== FAILURE LOG ==="
  journalctl -u vutrulabs-job-tracker-public.service -n 120 --no-pager
  echo "STOP: service did not finish successfully - DO NOT RETRY"
  exit 93
fi

echo "=== HYIMPULSE DATA QUALITY ==="
/opt/vutrulabs/job-tracker-public/.venv/bin/python - <<'PY'
import csv
import json
from pathlib import Path

base = Path("/opt/vutrulabs/job-tracker-public/data/hyimpulse/processed")

def read_csv(name):
    with (base / name).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))

latest = read_csv("jobs_latest.csv")
details = read_csv("job_details.csv")

apply_now = sum((r.get("title") or "").strip().upper() == "APPLY NOW" for r in latest)
unknown_location = sum((r.get("location") or "").strip().lower() == "unknown" for r in latest)
unknown_department = sum((r.get("department") or "").strip().lower() == "unknown" for r in latest)
missions = sum(bool((r.get("mission") or "").strip()) for r in details)
requirements = sum(bool((r.get("requirements") or "").strip()) for r in details)
benefits = sum(bool((r.get("benefits") or "").strip()) for r in details)

print(f"latest_rows={len(latest)}")
print(f"detail_rows={len(details)}")
print(f"apply_now_titles={apply_now}")
print(f"unknown_locations={unknown_location}")
print(f"unknown_departments={unknown_department}")
print(f"nonempty_mission={missions}")
print(f"nonempty_requirements={requirements}")
print(f"nonempty_benefits={benefits}")
print("sample_titles=")
for row in latest[:10]:
    print(" -", row.get("title", ""))

meta_path = base / "acquisition.json"
if not meta_path.exists():
    raise SystemExit("STOP: missing HyImpulse acquisition.json")
meta = json.loads(meta_path.read_text(encoding="utf-8"))
print("acquisition_status=", meta.get("status"))
print("acquisition_adapter=", meta.get("adapter"))
print("coverage_complete=", meta.get("coverage_complete"))

if not latest or len(latest) != len(details):
    raise SystemExit("STOP: HyImpulse latest/detail row counts are empty or inconsistent")
if apply_now or unknown_location or unknown_department:
    raise SystemExit("STOP: HyImpulse data still contains APPLY NOW / Unknown placeholders")
if not any((row.get("mission") or "").strip() for row in details):
    raise SystemExit("STOP: HyImpulse detail descriptions are missing")
if meta.get("adapter") != "personio_xml" or meta.get("status") != "success" or meta.get("coverage_complete") is not True:
    raise SystemExit("STOP: HyImpulse metadata does not confirm successful Personio collection")
print("HYIMPULSE DATA QUALITY OK")
PY

echo "=== FINAL GIT STATE ==="
git status --short
git fetch origin main
LOCAL_AFTER="$(git rev-parse HEAD)"
REMOTE_AFTER="$(git rev-parse origin/main)"
echo "local_after=$LOCAL_AFTER"
echo "remote_after=$REMOTE_AFTER"

if [ "$LOCAL_AFTER" != "$REMOTE_AFTER" ]; then
  echo "STOP: publication did not leave local and remote main aligned"
  exit 94
fi

echo "=== LATEST PUBLICATION COMMIT ==="
git log -1 --oneline

echo "=== TIMER AFTER MANUAL RUN (UTC) ==="
systemctl is-enabled vutrulabs-job-tracker-public.timer
TZ=UTC systemctl list-timers --all --no-pager vutrulabs-job-tracker-public.timer

echo "=== FINAL PUBLICATION LOG ==="
journalctl -u vutrulabs-job-tracker-public.service -n 80 --no-pager

echo "=== MANUAL PRODUCTION VERIFICATION COMPLETE ==="
```

---

## Expected success evidence

The run is accepted only if all of these are true:

- `systemctl_start_rc=0`
- service `Result=success`
- `ExecMainStatus=0`
- HyImpulse `latest_rows` is greater than zero
- `latest_rows == detail_rows`
- `apply_now_titles=0`
- `unknown_locations=0`
- `unknown_departments=0`
- `HYIMPULSE CONFIG OK` and `HYIMPULSE DATA QUALITY OK` are present; acquisition uses `personio_xml`, status `success`, and complete coverage
- at least one detail record contains a non-empty mission description
- the publication log reports a successful publication/push
- `local_after == remote_after`
- `git status --short` is empty
- the 48-hour timer remains enabled and has a future UTC execution

If any required condition fails, do not immediately rerun. Capture the non-secret output and investigate first.

## What to return for review

Return only non-secret evidence:

- service Result and ExecMainStatus
- latest/detail row counts
- APPLY NOW / Unknown counts
- non-empty detail counts
- sample job titles
- acquisition status/adapter/coverage flag
- latest publication commit SHA/message
- local/remote main SHA equality
- next timer execution in UTC

Do not return private profile contents, SSH material, tokens, or credentials.

---

## One-paste Hostinger launcher (single command)

**If the terminal shows a `>` continuation prompt, press `Ctrl+C` until the normal `root@...#` prompt returns.** Do not paste the previous `bash <<'HOSTINGER'` here-document; its terminator was not recognized in the browser terminal (`HOSTINGER^M`).

With the normal root prompt visible, copy and execute **this exact single command**. Do not break it into multiple commands. It requires a clean Git worktree, fast-forwards `main`, extracts only the **first** fenced bash block from this file, checks that the corrected HyImpulse validation exists, and executes that vetted runbook via `bash` with strict error handling. The primary runbook is the single source of truth.

```bash
cd /opt/vutrulabs/job-tracker-public && git switch main && test -z "$(git status --porcelain=v1 --untracked-files=all)" && git pull --ff-only origin main && python3 -c 'from pathlib import Path; import subprocess; text=Path("docs/HOSTINGER_PR15_IMMEDIATE_PRODUCTION_RUN.md").read_text(); parts=text.partition("```bash\n"); assert parts[1], "STOP: main bash block missing"; script=parts[2].split("\n```",1)[0]; assert "HYIMPULSE CONFIG OK" in script and "HYIMPULSE DATA QUALITY OK" in script, "STOP: outdated runbook"; subprocess.run(["bash","-e","-u","-o","pipefail"],input=script,text=True,check=True)'
```

Do **not** rerun if anything fails. Return the non-secret output for review. A successful Git pull alone is not proof that the production job has run.
